import json
import logging
from typing import Any, Optional
from .client import call_ruflo

logger = logging.getLogger(__name__)


async def store(key: str, value: Any) -> None:
    await call_ruflo("mcp__ruflo__memory_store", {"key": key, "value": json.dumps(value)})


async def retrieve(key: str) -> Optional[Any]:
    result = await call_ruflo("mcp__ruflo__memory_retrieve", {"key": key})
    if result and result.get("value"):
        try:
            return json.loads(result["value"])
        except (json.JSONDecodeError, TypeError):
            return result["value"]
    return None


async def delete(key: str) -> None:
    await call_ruflo("mcp__ruflo__memory_delete", {"key": key})
