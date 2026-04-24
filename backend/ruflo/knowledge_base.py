import json
import logging
from typing import Any, Optional
from .client import call_ruflo

logger = logging.getLogger(__name__)


async def store(namespace: str, key: str, value: Any) -> None:
    await call_ruflo("mcp__ruflo__agentdb_hierarchical-store", {
        "namespace": namespace,
        "key": key,
        "value": json.dumps(value) if not isinstance(value, str) else value
    })


async def recall(namespace: str, key: str) -> Optional[Any]:
    result = await call_ruflo("mcp__ruflo__agentdb_hierarchical-recall", {
        "namespace": namespace,
        "key": key
    })
    if result and result.get("value"):
        try:
            return json.loads(result["value"])
        except (json.JSONDecodeError, TypeError):
            return result["value"]
    return None


async def pattern_search(namespace: str, pattern: dict) -> list:
    result = await call_ruflo("mcp__ruflo__agentdb_pattern-search", {
        "namespace": namespace,
        "pattern": json.dumps(pattern)
    })
    return result.get("results", []) if result else []


async def synthesize(namespace: str, query: str) -> str:
    result = await call_ruflo("mcp__ruflo__agentdb_context-synthesize", {
        "namespace": namespace,
        "query": query
    })
    return result.get("synthesis", "") if result else ""
