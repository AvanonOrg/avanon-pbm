from fastapi import APIRouter, HTTPException, status
from storage.models import LoginRequest, TokenResponse
from api.middleware.auth import authenticate_user, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(user["tenant_id"], user["email"])
    return TokenResponse(access_token=token, tenant_id=user["tenant_id"])
