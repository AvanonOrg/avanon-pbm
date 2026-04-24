import uuid
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from storage.models import ChatRequest, ChatResponse
from agents.orchestrator import handle_message
from api.middleware.auth import get_tenant_id, get_current_user
import asyncio
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    if not request.session_id:
        request.session_id = str(uuid.uuid4())
    return await handle_message(request.message, request.session_id, tenant_id)


@router.websocket("/chat/stream/{session_id}")
async def chat_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time task progress updates."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            message = payload.get("message", "")
            tenant_id = payload.get("tenant_id", "unknown")

            # Stream a "thinking" ack immediately
            await websocket.send_json({"type": "ack", "status": "thinking"})

            response = await handle_message(message, session_id, tenant_id)

            await websocket.send_json({
                "type": "complete",
                "reply": response.reply,
                "report": response.report.model_dump() if response.report else None,
                "task_id": response.task_id,
                "task_status": response.task_status,
            })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
