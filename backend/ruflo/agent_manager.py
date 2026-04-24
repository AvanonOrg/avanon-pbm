import asyncio
import logging
from typing import Any, Optional
from .client import call_ruflo

logger = logging.getLogger(__name__)

POLL_INTERVAL = 3.0
MAX_WAIT_SECONDS = 120


async def spawn(task: str, params: dict) -> str:
    result = await call_ruflo("mcp__ruflo__agent_spawn", {"task": task, "params": params})
    agent_id = result.get("agent_id") if result else None
    logger.info(f"Spawned agent {agent_id} for task '{task}'")
    return agent_id


async def status(agent_id: str) -> dict:
    return await call_ruflo("mcp__ruflo__agent_status", {"agent_id": agent_id})


async def health(agent_id: str) -> dict:
    return await call_ruflo("mcp__ruflo__agent_health", {"agent_id": agent_id})


async def terminate(agent_id: str) -> None:
    await call_ruflo("mcp__ruflo__agent_terminate", {"agent_id": agent_id})


async def wait_for_result(agent_id: str) -> Any:
    elapsed = 0.0
    while elapsed < MAX_WAIT_SECONDS:
        s = await status(agent_id)
        if not s:
            break
        state = s.get("status", "")
        if state == "complete":
            return s.get("result")
        if state == "failed":
            logger.error(f"Agent {agent_id} failed: {s.get('error')}")
            return None
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    logger.warning(f"Agent {agent_id} timed out after {MAX_WAIT_SECONDS}s")
    return None


async def gather_agents(agent_ids: list[str]) -> list[Any]:
    return await asyncio.gather(*[wait_for_result(aid) for aid in agent_ids])
