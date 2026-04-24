import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import anthropic

from config import get_settings
from .system_prompt import SYSTEM_PROMPT
from .tool_definitions import CLAUDE_TOOLS
from ruflo import memory, knowledge_base, task_manager, workflow, agent_manager
from data.nadac_fetcher import fetch_nadac, calculate_total
from data.goodrx_scraper import scrape_goodrx
from data.medicaid_report_fetcher import get_citation_for_drug_class
from analysis.spread_calculator import calculate_spread
from analysis.report_builder import build_report
from storage.models import ChatResponse, DiscrepancyReport
from storage import supabase_client

logger = logging.getLogger(__name__)
settings = get_settings()
client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

MEM_CONV_PREFIX = "conv"
KB_PRICING = "drug_pricing"


async def handle_message(user_message: str, session_id: str, tenant_id: str) -> ChatResponse:
    # Load conversation history
    history = await memory.retrieve(f"{MEM_CONV_PREFIX}:{session_id}") or []

    history.append({"role": "user", "content": user_message})

    # Create a task to track progress
    task_id = await task_manager.create(
        title=f"Researching: {user_message[:60]}",
        description=user_message,
        tenant_id=tenant_id,
    )

    report: Optional[DiscrepancyReport] = None
    active_tasks: list[str] = [task_id] if task_id else []

    try:
        await task_manager.update(task_id, "running", 10, "Analyzing request...")
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=history,
            tools=CLAUDE_TOOLS,
        )

        # Agentic tool-use loop
        loop_count = 0
        while response.stop_reason == "tool_use" and loop_count < 10:
            loop_count += 1
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                progress = min(20 + loop_count * 15, 85)
                await task_manager.update(task_id, "running", progress, f"Running: {block.name}")

                result = await _execute_tool(block.name, block.input, tenant_id, user_message)

                # Capture report if generated
                if block.name == "generate_discrepancy_report" and isinstance(result, dict) and "report_id" in result:
                    report = DiscrepancyReport(**result)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

            # Feed results back to Claude
            updated_messages = history + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]
            response = await client.messages.create(
                model=settings.claude_model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=updated_messages,
                tools=CLAUDE_TOOLS,
            )

        # Extract final text reply
        reply = next(
            (b.text for b in response.content if hasattr(b, "text")),
            "I wasn't able to generate a response. Please try again."
        )

        # Save updated conversation history
        history.append({"role": "assistant", "content": reply})
        await memory.store(f"{MEM_CONV_PREFIX}:{session_id}", history[-20:])  # keep last 20 turns

        await task_manager.complete(task_id, {"reply": reply, "report_id": report.report_id if report else None})

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            report=report,
            task_id=task_id,
            task_status="complete",
        )

    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        if task_id:
            await task_manager.update(task_id, "failed", 0, str(e))
        return ChatResponse(
            reply="I encountered an error while researching that. Please try again.",
            session_id=session_id,
            task_id=task_id,
            task_status="failed",
        )


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

    # Check pricing KB
    cached = await knowledge_base.recall(KB_PRICING, query.lower().replace(" ", "/"))
    if cached:
        captured = datetime.fromisoformat(cached.get("captured_at", "2000-01-01"))
        if captured > cutoff:
            return {"found": True, "data": cached}

    # Check Medicaid reports KB
    medicaid = await knowledge_base.synthesize("medicaid_pbm_reports", query)
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
    return {
        **result,
        "quantity": quantity,
        "nadac_total": total,
    }


async def _tool_search_prices(inputs: dict) -> dict:
    drug_name = inputs.get("drug_name", "")
    strength = inputs.get("strength", "")
    quantity = inputs.get("quantity", 30)

    # Spawn GoodRx agent (parallel)
    goodrx_id = await agent_manager.spawn("goodrx_scraper", {
        "drug_name": drug_name,
        "strength": strength,
        "quantity": quantity,
    })

    # Wait for results
    results = {}
    if goodrx_id:
        goodrx_result = await agent_manager.wait_for_result(goodrx_id)
        if goodrx_result:
            results["goodrx"] = goodrx_result
        else:
            # Fallback: direct scrape
            direct = await scrape_goodrx(drug_name, strength, quantity)
            if direct:
                results["goodrx"] = direct

    return results or {"warning": "Could not retrieve prices from external sources"}


async def _tool_create_monitoring(inputs: dict, tenant_id: str) -> dict:
    drug_name = inputs.get("drug_name", "")
    frequency = inputs.get("frequency", "weekly")

    schedule_map = {"daily": "0 9 * * *", "weekly": "0 9 * * 1", "biweekly": "0 9 1,15 * *", "monthly": "0 9 1 * *"}
    cron = schedule_map.get(frequency, "0 9 * * 1")

    workflow_id = await workflow.create(
        name=f"monitor_{drug_name.lower().replace(' ', '_')}_{tenant_id[:8]}",
        steps=[
            {"action": "fetch_nadac", "params": {"drug_name": drug_name}},
            {"action": "scrape_goodrx", "params": {"drug_name": drug_name}},
            {"action": "calculate_spread", "depends_on": ["fetch_nadac", "scrape_goodrx"]},
            {"action": "store_snapshot", "depends_on": ["calculate_spread"]},
            {"action": "alert_if_change", "depends_on": ["store_snapshot"]},
        ],
        schedule=cron,
    )

    task_id = await task_manager.create(
        title=f"Monitoring {drug_name} ({frequency})",
        description=f"Recurring price monitoring for {drug_name}",
        tenant_id=tenant_id,
    )

    return {
        "success": True,
        "drug_name": drug_name,
        "frequency": frequency,
        "workflow_id": workflow_id,
        "task_id": task_id,
        "message": f"Monitoring set up for {drug_name}. I'll check prices {frequency} and alert you on changes.",
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

        # Store in knowledge base for future cache hits
        kb_key = f"{d.get('drug_name', '').lower().replace(' ', '/')}"
        await knowledge_base.store(KB_PRICING, kb_key, {
            **analysis.model_dump(),
            "captured_at": datetime.utcnow().isoformat(),
        })

    report = build_report(query=query, tenant_id=tenant_id, analyses=analyses)

    # Persist to Supabase
    drugs_data = [a.model_dump() for a in analyses]
    await supabase_client.save_report(
        report_id=report.report_id,
        tenant_id=tenant_id,
        query=query,
        summary=report.summary,
        drugs_json=drugs_data,
        recommendation=report.recommendation,
        total_savings=report.total_annual_savings_100_members,
    )
    # Also save pricing snapshots
    for a in analyses:
        await supabase_client.insert_pricing_snapshot(
            drug_name=a.drug_name,
            ndc=a.ndc,
            strength=a.strength,
            quantity=a.quantity,
            source="goodrx",
            price=a.goodrx_lowest or a.plan_price_estimate or 0,
            price_per_unit=None,
        )

    return report.model_dump()
