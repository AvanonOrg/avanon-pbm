from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from storage import supabase_client
from api.middleware.auth import get_tenant_id

router = APIRouter(prefix="/api", tags=["prospects"])


@router.get("/prospects/list")
async def list_prospects(
    tenant_id: str = Depends(get_tenant_id),
    pbm: Optional[str] = Query(None, description="Filter by PBM (CVS Caremark | Express Scripts | OptumRx)"),
    state: Optional[str] = Query(None, description="Filter by 2-letter state code"),
    plan_type: Optional[str] = Query(None, description="self-insured | fully-insured"),
    min_employees: Optional[int] = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List prospects for this tenant, sorted by estimated annual overpayment desc.

    Backed by the `prospects` table seeded from Form 5500 Schedule C filings
    (employer → PBM service-provider mapping joined with plan headcount).
    """
    rows = await supabase_client.list_prospects(
        tenant_id=tenant_id,
        pbm=pbm,
        state=state,
        plan_type=plan_type,
        min_employees=min_employees,
        limit=limit,
    )
    return {"prospects": rows, "count": len(rows)}


@router.get("/prospects/summary")
async def prospects_summary(tenant_id: str = Depends(get_tenant_id)):
    """Aggregate pipeline metrics: total prospects, total addressable savings, breakdown by PBM."""
    summary = await supabase_client.get_prospects_summary(tenant_id)
    return summary


@router.get("/prospects/{prospect_id}")
async def get_prospect(prospect_id: str, tenant_id: str = Depends(get_tenant_id)):
    row = await supabase_client.get_prospect(prospect_id, tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return row
