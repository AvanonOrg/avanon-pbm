from fastapi import APIRouter, Depends, HTTPException
from storage import supabase_client
from api.middleware.auth import get_tenant_id

router = APIRouter(prefix="/api", tags=["tasks"])


@router.get("/tasks")
async def list_tasks(tenant_id: str = Depends(get_tenant_id)):
    return await supabase_client.list_tasks(tenant_id)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, tenant_id: str = Depends(get_tenant_id)):
    task = await supabase_client.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
