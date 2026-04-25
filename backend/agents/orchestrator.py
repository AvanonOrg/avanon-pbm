import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import anthropic

from config import get_settings
from .system_prompt import SYSTEM_PROMPT
from .tool_definitions import CLAUDE_TOOLS
from storage import supabase_client
from storage import kb_cache
from data.nadac_fetcher import fetch_nadac, calculate_total
from data.goodrx_scraper import scrape_goodrx
from data.medicaid_report_fetcher import get_citation_for_drug_class
from analysis.spread_calculator import calculate_spread
from analysis.report_builder import build_report
from storage.models import ChatResponse, DiscrepancyReport

logger = logging.getLogger(__name__)
settings = get_settings()
client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

KB_PRICING = "drug_pricing"


# ── Conversation memory (Supabase) ──────────────────────────────────────────

async def _retrieve_history(session_id: str) -> list:
    try:
        return await supabase_client.get_conversation(session_id)
    except Exception:
        return []


async def _store_history(session_id: str, tenant_id: str, messages: list) -> None:
    try:
        await supabase_client.save_conversation(session_id, tenant_id, messages[-20:])
    except Exception:
        pass


# ── Task tracking (Supabase) ────────────────────────────────────────────────

async def _create_task(tenant_id: str, title: str, description: str) -> Optional[str]:
    task_id = f"task_{uuid4().hex[:12]}"
    try:
        await supabase_client.upsert_task(
            task_id=task_id, tenant_id=tenant_id,
            title=title, description=description,
            status="pending", progress=0,
        )
        return task_id
    except Exception:
        return None


async def _update_task(task_id: str, tenant_id: str, status: str, progress: int = 0, step: str = "") -> None:
    try:
        await supabase_client.upsert_task(
            task_id=task_id, tenant_id=tenant_id,
            title="", description="",
            status=status, progress=progress, current_step=step,
        )
    except Exception:
        pass


async def _complete_task(task_id: str, tenant_id: str, result: dict) -> None:
    try:
        await supabase_client.upsert_task(
            task_id=task_id, tenant_id=tenant_id,
            title="", description="",
            status="complete", progress=100,
            result_report_id=result.get("report_id"),
            completed_at=datetime.utcnow(),
        )
    except Exception:
        pass


# ── Streaming entry point ────────────────────────────────────────────────────

def _tool_step_label(tool_name: str, tool_input: dict) -> str:
    labels = {
        "search_knowledge_base": lambda i: f"Searching knowledge base for {i.get('query', '')}…",
        "fetch_nadac_baseline": lambda i: f"Fetching NADAC baseline for {i.get('drug_name', '')}…",
        "search_drug_prices": lambda i: f"Searching drug prices for {i.get('drug_name', '')}…",
        "create_monitoring_task": lambda i: f"Setting up monitoring for {i.get('drug_name', '')}…",
        "generate_discrepancy_report": lambda i: "Generating discrepancy report…",
    }
    fn = labels.get(tool_name)
    return fn(tool_input) if fn else f"Running {tool_name}…"


async def handle_message_stream(user_message: str, session_id: str, tenant_id: str, client_history: list = []):
    """Async generator that yields SSE event dicts for the streaming endpoint."""
    if client_history:
        history = list(client_history)
    else:
        history = await _retrieve_history(session_id)
    history.append({"role": "user", "content": user_message})

    task_id = await _create_task(tenant_id, f"Researching: {user_message[:60]}", user_message)

    async def _track(status: str, progress: int = 0, step: str = "") -> None:
        if not task_id:
            return
        await _update_task(task_id, tenant_id, status, progress, step)

    report: Optional[DiscrepancyReport] = None
    current_messages = list(history)
    full_reply = ""
    loop_count = 0

    try:
        await _track("running", 10, "Analyzing request…")

        # Single streaming loop — no separate messages.create() planning call.
        # stream() handles tool-use rounds and final text in one loop.
        while loop_count <= 10:
            loop_count += 1

            async with client.messages.stream(
                model=settings.claude_model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=current_messages,
                tools=CLAUDE_TOOLS,
            ) as stream:
                async for chunk in stream.text_stream:
                    full_reply += chunk
                    yield {"type": "text_delta", "delta": chunk}

                final_msg = await stream.get_final_message()

            if final_msg.stop_reason != "tool_use":
                break

            # Execute all requested tools
            tool_results = []
            for block in final_msg.content:
                if block.type != "tool_use":
                    continue

                progress = min(20 + loop_count * 15, 85)
                await _track("running", progress, f"Running: {block.name}")
                yield {"type": "thinking", "step": _tool_step_label(block.name, block.input), "tool": block.name}

                result = await _execute_tool(block.name, block.input, tenant_id, user_message)

                if block.name == "generate_discrepancy_report" and isinstance(result, dict) and "report_id" in result:
                    report = DiscrepancyReport(**result)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

            current_messages = current_messages + [
                {"role": "assistant", "content": final_msg.content},
                {"role": "user", "content": tool_results},
            ]
            full_reply = ""  # reset — next iteration streams the real answer

        history.append({"role": "assistant", "content": full_reply})
        await _store_history(session_id, tenant_id, history)
        if task_id:
            await _complete_task(task_id, tenant_id, {"report_id": report.report_id if report else None})

        yield {
            "type": "done",
            "reply": full_reply,
            "report": report.model_dump() if report else None,
            "task_id": task_id,
            "task_status": "complete",
        }

    except Exception as e:
        logger.error(f"Stream orchestrator error: {e}", exc_info=True)
        await _track("failed", 0, str(e))
        yield {"type": "error", "message": str(e)}


# ── Non-streaming entry point ────────────────────────────────────────────────

async def handle_message(user_message: str, session_id: str, tenant_id: str) -> ChatResponse:
    history = await _retrieve_history(session_id)
    history.append({"role": "user", "content": user_message})

    task_id = await _create_task(tenant_id, f"Researching: {user_message[:60]}", user_message)
    report: Optional[DiscrepancyReport] = None

    try:
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=history,
            tools=CLAUDE_TOOLS,
        )

        loop_count = 0
        while response.stop_reason == "tool_use" and loop_count < 10:
            loop_count += 1
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue
                result = await _execute_tool(block.name, block.input, tenant_id, user_message)
                if block.name == "generate_discrepancy_report" and isinstance(result, dict) and "report_id" in result:
                    report = DiscrepancyReport(**result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

            updated = history + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]
            response = await client.messages.create(
                model=settings.claude_model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=updated,
                tools=CLAUDE_TOOLS,
            )

        reply = next(
            (b.text for b in response.content if hasattr(b, "text")),
            "I wasn't able to generate a response. Please try again."
        )

        history.append({"role": "assistant", "content": reply})
        await _store_history(session_id, tenant_id, history)
        if task_id:
            await _complete_task(task_id, tenant_id, {"report_id": report.report_id if report else None})

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            report=report,
            task_id=task_id,
            task_status="complete",
        )

    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        return ChatResponse(
            reply="I encountered an error while researching that. Please try again.",
            session_id=session_id,
            task_id=task_id,
            task_status="failed",
        )


# ── Tool dispatch ────────────────────────────────────────────────────────────

async def _execute_tool(tool_name: str, tool_input: dict, tenant_id: str, original_query: str) -> dict:
    try:
        if tool_name == "search_knowledge_base":
            return await _tool_search_kb(tool_input)
        elif tool_name == "fetch_nadac_baseline":
            return await _tool_fetch_nadac(tool_input)
        elif tool_name == "search_drug_prices":
            return await _tool_search_prices(tool_input)
        elif tool_name == "create_monitoring_task":
            return await _tool_create_monitoring(tool_input, tenant_id)
        elif tool_name == "generate_discrepancy_report":
            return await _tool_generate_report(tool_input, tenant_id, original_query)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
        return {"error": str(e)}


async def _tool_search_kb(inputs: dict) -> dict:
    query = inputs.get("query", "")
    max_age_days = inputs.get("max_age_days", 7)
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)

    cached = await kb_cache.recall(KB_PRICING, query.lower().replace(" ", "/"))
    if cached:
        captured = datetime.fromisoformat(cached.get("captured_at", "2000-01-01"))
        if captured > cutoff:
            return {"found": True, "data": cached}

    medicaid = await kb_cache.synthesize("medicaid_pbm_reports", query)
    if medicaid:
        return {"found": True, "medicaid_context": medicaid}

    return {"found": False, "message": "No recent cached data. Fetch fresh data."}


async def _tool_fetch_nadac(inputs: dict) -> dict:
    drug_name = inputs.get("drug_name", "")
    ndc = inputs.get("ndc")
    quantity = inputs.get("quantity", 30)

    result = await fetch_nadac(drug_name, ndc)
    if not result:
        return {"error": f"NADAC data not found for '{drug_name}'"}

    total = calculate_total(result["nadac_per_unit"], quantity)
    return {**result, "quantity": quantity, "nadac_total": total}


async def _tool_search_prices(inputs: dict) -> dict:
    drug_name = inputs.get("drug_name", "")
    strength = inputs.get("strength", "")
    quantity = inputs.get("quantity", 30)

    results = {}
    direct = await scrape_goodrx(drug_name, strength, quantity)
    if direct:
        results["goodrx"] = direct

    return results or {"warning": "GoodRx prices unavailable. Using NADAC as sole pricing benchmark."}


async def _tool_create_monitoring(inputs: dict, tenant_id: str) -> dict:
    drug_name = inputs.get("drug_name", "")
    frequency = inputs.get("frequency", "weekly")

    task_id = await _create_task(
        tenant_id,
        title=f"Monitoring {drug_name} ({frequency})",
        description=f"Recurring price monitoring for {drug_name}",
    )

    return {
        "success": True,
        "drug_name": drug_name,
        "frequency": frequency,
        "task_id": task_id,
        "message": (
            f"Monitoring set up for {drug_name}. "
            f"I'll check prices {frequency} and alert you on changes."
        ),
    }


async def _tool_generate_report(inputs: dict, tenant_id: str, original_query: str) -> dict:
    drugs_input = inputs.get("drugs", [])
    query = inputs.get("query", original_query)

    analyses = []
    for d in drugs_input:
        citation = await get_citation_for_drug_class(d.get("drug_name", ""))
        analysis = calculate_spread(
            drug_name=d.get("drug_name", "Unknown"),
            nadac_per_unit=float(d.get("nadac_per_unit", 0)),
            quantity=int(d.get("quantity", 30)),
            plan_price=d.get("plan_price"),
            goodrx_lowest=d.get("goodrx_lowest"),
            ndc=d.get("ndc"),
            strength=d.get("strength", ""),
            medicaid_citation=citation,
        )
        analyses.append(analysis)

        await kb_cache.store(KB_PRICING, d.get("drug_name", "").lower().replace(" ", "/"), {
            **analysis.model_dump(),
            "captured_at": datetime.utcnow().isoformat(),
        })

    report = build_report(query=query, tenant_id=tenant_id, analyses=analyses)

    drugs_data = [a.model_dump() for a in analyses]
    try:
        await supabase_client.save_report(
            report_id=report.report_id,
            tenant_id=tenant_id,
            query=query,
            summary=report.summary,
            drugs_json=drugs_data,
            recommendation=report.recommendation,
            total_savings=report.total_annual_savings_100_members,
        )
    except Exception as e:
        logger.warning(f"Report save failed (non-fatal): {e}")

    for a in analyses:
        try:
            await supabase_client.insert_pricing_snapshot(
                drug_name=a.drug_name,
                ndc=a.ndc,
                strength=a.strength,
                quantity=a.quantity,
                source="goodrx",
                price=a.goodrx_lowest or a.plan_price_estimate or 0,
                price_per_unit=None,
            )
        except Exception as e:
            logger.warning(f"Pricing snapshot save failed (non-fatal): {e}")

    return report.model_dump()
