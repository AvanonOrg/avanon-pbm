import logging
from typing import Optional
from .client import call_ruflo

logger = logging.getLogger(__name__)


async def create(name: str, steps: list, schedule: Optional[str] = None) -> str:
    params = {"name": name, "steps": steps}
    if schedule:
        params["schedule"] = schedule
    result = await call_ruflo("mcp__ruflo__workflow_create", params)
    return result.get("workflow_id") if result else None


async def execute(workflow_id: str) -> dict:
    return await call_ruflo("mcp__ruflo__workflow_execute", {"workflow_id": workflow_id}) or {}


async def run(workflow_id: str) -> dict:
    return await call_ruflo("mcp__ruflo__workflow_run", {"workflow_id": workflow_id}) or {}


async def get_status(workflow_id: str) -> dict:
    return await call_ruflo("mcp__ruflo__workflow_status", {"workflow_id": workflow_id}) or {}


async def list_workflows() -> list:
    result = await call_ruflo("mcp__ruflo__workflow_list", {})
    return result.get("workflows", []) if result else []
