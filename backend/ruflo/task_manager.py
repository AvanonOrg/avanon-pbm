"""
Task manager: dual-writes to both ruflo MCP (for agent coordination) and
Supabase (for persistent tenant-scoped task history the API can query).
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Any

from .client import call_ruflo

logger = logging.getLogger(__name__)


async def create(title: str, description: str, tenant_id: str) -> str:
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    # Ruflo (best-effort — doesn't block if ruflo is unavailable)
    try:
        result = await call_ruflo("mcp__ruflo__task_create", {
            "task_id": task_id,
            "title": title,
            "description": description,
            "metadata": {"tenant_id": tenant_id}
        })
        if result and result.get("task_id"):
            task_id = result["task_id"]
    except Exception as e:
        logger.warning(f"Ruflo task_create failed (using generated ID): {e}")

    # Supabase — always write
    from storage import supabase_client
    await supabase_client.upsert_task(
        task_id=task_id,
        tenant_id=tenant_id,
        title=title,
        description=description,
        status="pending",
        progress=0,
    )
    return task_id


async def update(task_id: str, status: str, progress: int, current_step: str = "") -> None:
    try:
        await call_ruflo("mcp__ruflo__task_update", {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "current_step": current_step
        })
    except Exception as e:
        logger.warning(f"Ruflo task_update failed: {e}")

    from storage import supabase_client
    await supabase_client.upsert_task(
        task_id=task_id,
        tenant_id="",  # already exists, update only these fields
        title="",
        description="",
        status=status,
        progress=progress,
        current_step=current_step,
    )


async def complete(task_id: str, result: Any) -> None:
    result_str = json.dumps(result, default=str) if not isinstance(result, str) else result
    try:
        await call_ruflo("mcp__ruflo__task_complete", {"task_id": task_id, "result": result_str})
    except Exception as e:
        logger.warning(f"Ruflo task_complete failed: {e}")

    report_id = result.get("report_id") if isinstance(result, dict) else None
    from storage import supabase_client
    await supabase_client.upsert_task(
        task_id=task_id,
        tenant_id="",
        title="",
        description="",
        status="complete",
        progress=100,
        result_report_id=report_id,
        completed_at=datetime.utcnow(),
    )


async def get_status(task_id: str) -> dict:
    # Supabase is authoritative for status queries
    from storage import supabase_client
    row = await supabase_client.get_task(task_id)
    if row:
        return row
    # Fallback to ruflo
    try:
        result = await call_ruflo("mcp__ruflo__task_status", {"task_id": task_id})
        return result or {}
    except Exception:
        return {}


async def list_tasks(tenant_id: Optional[str] = None) -> list:
    from storage import supabase_client
    return await supabase_client.list_tasks(tenant_id or "")
