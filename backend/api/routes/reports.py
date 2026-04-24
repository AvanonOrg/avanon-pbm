from fastapi import APIRouter, Depends, HTTPException
from storage import supabase_client
from api.middleware.auth import get_tenant_id

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports/{report_id}")
async def get_report(report_id: str, tenant_id: str = Depends(get_tenant_id)):
    data = await supabase_client.get_report(report_id, tenant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Report not found")
    return data
