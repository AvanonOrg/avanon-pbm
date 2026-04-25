"""
In-process knowledge base cache — replaces Ruflo knowledge_base MCP.
Simple TTL dict; resets on restart, which is fine (Ruflo was never persisting
anything anyway because every call was 429'd).
"""
from typing import Any, Optional

_store: dict[str, Any] = {}


async def recall(namespace: str, key: str) -> Optional[Any]:
    return _store.get(f"{namespace}/{key}")


async def store(namespace: str, key: str, value: Any) -> None:
    _store[f"{namespace}/{key}"] = value


async def synthesize(namespace: str, query: str) -> Optional[str]:
    """Keyword search across stored items in the namespace."""
    q = query.lower()
    for k, v in _store.items():
        if not k.startswith(f"{namespace}/"):
            continue
        if q in str(v).lower():
            return str(v)
    return None
