import asyncio
import logging
from typing import Optional
from .client import call_ruflo

logger = logging.getLogger(__name__)


async def open_url(url: str) -> dict:
    return await call_ruflo("mcp__ruflo__browser_open", {"url": url})


async def get_text(selector: Optional[str] = None) -> str:
    params = {}
    if selector:
        params["selector"] = selector
    result = await call_ruflo("mcp__ruflo__browser_get-text", params)
    return result.get("text", "") if result else ""


async def snapshot() -> dict:
    return await call_ruflo("mcp__ruflo__browser_snapshot", {})


async def fill(selector: str, value: str) -> None:
    await call_ruflo("mcp__ruflo__browser_fill", {"selector": selector, "value": value})
    await asyncio.sleep(0.5)  # human-like delay


async def click(selector: str) -> None:
    await call_ruflo("mcp__ruflo__browser_click", {"selector": selector})
    await asyncio.sleep(0.8)


async def wait(milliseconds: int = 2000) -> None:
    await call_ruflo("mcp__ruflo__browser_wait", {"milliseconds": milliseconds})


async def close() -> None:
    await call_ruflo("mcp__ruflo__browser_close", {})
