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
            min_size=0,
            max_size=10,
            max_lifetime=300,
            max_idle=60,
            check=AsyncConnectionPool.check_connection,
            kwargs={"row_factory": dict_row, "prepare_threshold": None},
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


# ── Prospects ────────────────────────────────────────────────────────────────
async def list_prospects(
    tenant_id: str,
    pbm: Optional[str] = None,
    state: Optional[str] = None,
    plan_type: Optional[str] = None,
    min_employees: Optional[int] = None,
    limit: int = 100,
) -> list:
    """Return prospects for a tenant sorted by estimated overpayment desc."""
    pool = await get_pool()
    where = ["tenant_id = %s"]
    params: list[Any] = [tenant_id]
    if pbm:
        where.append("pbm = %s")
        params.append(pbm)
    if state:
        where.append("UPPER(state) = UPPER(%s)")
        params.append(state)
    if plan_type:
        where.append("plan_type = %s")
        params.append(plan_type)
    if min_employees is not None:
        where.append("employees >= %s")
        params.append(min_employees)
    params.append(limit)
    sql = (
        "SELECT id, company_name, ein, state, pbm, plan_type, employees, "
        "annual_drug_spend, estimated_spread_overpayment, cfo_email, chro_email, "
        "form_5500_year, source, created_at "
        f"FROM prospects WHERE {' AND '.join(where)} "
        "ORDER BY estimated_spread_overpayment DESC NULLS LAST LIMIT %s"
    )
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, tuple(params))
            return await cur.fetchall()


async def get_prospect(prospect_id: str, tenant_id: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM prospects WHERE id = %s AND tenant_id = %s",
                (prospect_id, tenant_id),
            )
            return await cur.fetchone()


async def get_prospects_summary(tenant_id: str) -> dict:
    """Pipeline metrics: total prospects, total covered lives, total overpayment, by-PBM breakdown."""
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT
                    COUNT(*) AS total_prospects,
                    COALESCE(SUM(employees), 0) AS total_covered_lives,
                    COALESCE(SUM(annual_drug_spend), 0) AS total_drug_spend,
                    COALESCE(SUM(estimated_spread_overpayment), 0) AS total_overpayment
                FROM prospects WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            totals = await cur.fetchone() or {}
            await cur.execute(
                """
                SELECT pbm,
                       COUNT(*) AS prospect_count,
                       COALESCE(SUM(employees), 0) AS covered_lives,
                       COALESCE(SUM(estimated_spread_overpayment), 0) AS overpayment
                FROM prospects WHERE tenant_id = %s
                GROUP BY pbm ORDER BY overpayment DESC
                """,
                (tenant_id,),
            )
            by_pbm = await cur.fetchall()
    return {"totals": totals, "by_pbm": by_pbm}
