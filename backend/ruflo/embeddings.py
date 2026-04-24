import logging
from typing import Optional
from .client import call_ruflo

logger = logging.getLogger(__name__)


async def search(query: str, namespace: str, top_k: int = 3) -> list:
    result = await call_ruflo("mcp__ruflo__embeddings_search", {
        "query": query,
        "namespace": namespace,
        "top_k": top_k
    })
    return result.get("results", []) if result else []


async def generate(text: str) -> list:
    result = await call_ruflo("mcp__ruflo__embeddings_generate", {"text": text})
    return result.get("embedding", []) if result else []


async def init(namespace: str) -> None:
    await call_ruflo("mcp__ruflo__embeddings_init", {"namespace": namespace})
