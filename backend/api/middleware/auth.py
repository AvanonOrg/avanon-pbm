from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer()

# Demo users — replace with Airtable/DB lookup in production
DEMO_USERS = {
    "demo@avanon.ai": {
        "password": "pbm2026!",
        "tenant_id": "tenant_demo",
        "name": "Demo Employer",
    },
    "costplus@avanon.ai": {
        "password": "markc2026!",
        "tenant_id": "tenant_costplus",
        "name": "Cost Plus Drugs",
    },
}


def create_token(tenant_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": email, "tenant_id": tenant_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    return verify_token(credentials.credentials)


def get_tenant_id(user: dict = Depends(get_current_user)) -> str:
    return user["tenant_id"]


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(email)
    if user and user["password"] == password:
        return {"email": email, **user}
    return None
