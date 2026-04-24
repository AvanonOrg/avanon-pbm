from fastapi import APIRouter, Depends, HTTPException
from ruflo import task_manager
from api.middleware.auth import get_tenant_id

router = APIRouter(prefix="/api", tags=["tasks"])


@router.get("/tasks")
async def list_tasks(tenant_id: str = Depends(get_tenant_id)):
    return await task_manager.list_tasks(tenant_id=tenant_id)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, tenant_id: str = Depends(get_tenant_id)):
    status = await task_manager.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status
