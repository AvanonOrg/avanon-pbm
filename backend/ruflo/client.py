"""
Ruflo MCP client using the MCP Python SDK with SSE (HTTP) transport.
Connects to https://mcpmarket.com/server/ruflo as a proper MCP server.
"""
import asyncio
import logging
from typing import Any
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_RETRIES = 1
RETRY_DELAY = 0.5

# Strip trailing slash
_MCP_URL = settings.ruflo_mcp_url.rstrip("/")


async def call_ruflo(tool_name: str, params: dict) -> Any:
    """
    Call a ruflo MCP tool by name with the given params.
    Opens a fresh SSE session per call (stateless; swap to a persistent session pool if latency matters).
    """
    # MCP tool names in the server are the short names (without the mcp__ruflo__ prefix)
    short_name = tool_name.replace("mcp__ruflo__", "")

    for attempt in range(MAX_RETRIES):
        try:
            async with sse_client(_MCP_URL) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(short_name, arguments=params)
                    # MCP returns a list of content blocks; extract text from the first
                    if result and result.content:
                        import json
                        text = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
                        try:
                            return json.loads(text)
                        except (json.JSONDecodeError, TypeError):
                            return {"value": text}
                    return None
        except Exception as e:
            logger.warning(f"Ruflo tool '{short_name}' error (attempt {attempt + 1}): {e}")
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Ruflo tool '{short_name}' failed after {MAX_RETRIES} attempts")
                return None
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    return None
