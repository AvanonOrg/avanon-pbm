"""
Direct PostgreSQL client using psycopg3 (binary wheels, no compilation on Windows).
Uses the Supabase DB connection string — no API key needed.
"""
import json
import logging
from datetime import datetime
from typing import Optional, Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: Optional[AsyncConnectionPool] = None


async def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            settings.supabase_db_url,
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=False,
        )
        await _pool.open()
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Tasks ─────────────────────────────────────────────────────────────────────

async def upsert_task(task_id: str, tenant_id: str, title: str, description: str,
                      status: str = "pending", progress: int = 0,
                      current_step: str = "", result_report_id: Optional[str] = None,
                      completed_at: Optional[datetime] = None) -> None:
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute("""
            INSERT INTO tasks (task_id, tenant_id, title, description, status, progress, current_step, result_report_id, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (task_id) DO UPDATE SET
                status = EXCLUDED.status,
                progress = EXCLUDED.progress,
                current_step = EXCLUDED.current_step,
                result_report_id = COALESCE(EXCLUDED.result_report_id, tasks.result_report_id),
                completed_at = COALESCE(EXCLUDED.completed_at, tasks.completed_at)
        """, (task_id, tenant_id or "", title or "", description or "",
              status, progress, current_step or "", result_report_id, completed_at))


async def get_task(task_id: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
            return await cur.fetchone()


async def list_tasks(tenant_id: str) -> list:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM tasks WHERE tenant_id = %s ORDER BY created_at DESC LIMIT 50",
                (tenant_id,)
            )
            return await cur.fetchall()


# ── Pricing Snapshots ─────────────────────────────────────────────────────────

async def insert_pricing_snapshot(drug_name: str, ndc: Optional[str], strength: Optional[str],
                                  quantity: int, source: str, price: float,
                                  price_per_unit: Optional[float] = None,
                                  pharmacy: Optional[str] = None, state: Optional[str] = None) -> None:
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute("""
            INSERT INTO pricing_snapshots (drug_name, ndc, strength, quantity, source, price, price_per_unit, pharmacy, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (drug_name, ndc, strength, quantity, source, price, price_per_unit, pharmacy, state))


# ── Reports ───────────────────────────────────────────────────────────────────

async def save_report(report_id: str, tenant_id: str, query: str, summary: str,
                      drugs_json: Any, recommendation: str, total_savings: float) -> None:
    pool = await get_pool()
    drugs_str = json.dumps(drugs_json, default=str) if not isinstance(drugs_json, str) else drugs_json
    async with pool.connection() as conn:
        await conn.execute("""
            INSERT INTO reports (report_id, tenant_id, query, summary, drugs_json, recommendation, total_annual_savings)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (report_id) DO NOTHING
        """, (report_id, tenant_id, query, summary, drugs_str, recommendation, total_savings))


async def get_report(report_id: str, tenant_id: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM reports WHERE report_id = %s AND tenant_id = %s",
                (report_id, tenant_id)
            )
            row = await cur.fetchone()
            if row and isinstance(row.get("drugs_json"), str):
                row["drugs_json"] = json.loads(row["drugs_json"])
            return row


# ── Conversations ─────────────────────────────────────────────────────────────

async def save_conversation(session_id: str, tenant_id: str, messages: list) -> None:
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute("""
            INSERT INTO conversations (session_id, tenant_id, messages_json)
            VALUES (%s, %s, %s::jsonb)
            ON CONFLICT (session_id) DO UPDATE SET messages_json = EXCLUDED.messages_json
        """, (session_id, tenant_id, json.dumps(messages, default=str)))


async def get_conversation(session_id: str) -> list:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT messages_json FROM conversations WHERE session_id = %s", (session_id,)
            )
            row = await cur.fetchone()
            if not row:
                return []
            msgs = row["messages_json"]
            return msgs if isinstance(msgs, list) else json.loads(msgs)
