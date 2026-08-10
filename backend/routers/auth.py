"""
auth.py — JWT Authentication for the Admin Dashboard
- POST /api/auth/login   → Accepts username+password, returns JWT
- GET  /api/auth/verify  → Verifies a token is still valid
- get_current_admin()    → FastAPI dependency to protect any route
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ── Token helpers ─────────────────────────────────────────────────────────────

def _create_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> Optional[str]:
    """Returns the username encoded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── Dependency: protect admin routes ─────────────────────────────────────────

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency. Add to any route:
        current_admin: str = Depends(get_current_admin)
    Returns the admin username, or raises 401 if the token is missing/invalid.
    """
    username = _decode_token(credentials.credentials)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="Admin Login")
def login(body: LoginRequest):
    """
    Accepts admin username and password.
    Returns a JWT token on success, or 401 on failure.
    """
    if (
        body.username != settings.ADMIN_USERNAME
        or body.password != settings.ADMIN_PASSWORD
    ):
        logger.warning(f"Failed login attempt for username: '{body.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    token = _create_token(body.username)
    logger.info(f"Admin '{body.username}' logged in successfully.")
    return TokenResponse(access_token=token, username=body.username)


@router.get("/verify", summary="Verify Token")
def verify(current_admin: str = Depends(get_current_admin)):
    """
    Lightweight endpoint for the frontend to check if the stored token is still valid.
    Returns 200 with the username, or 401 if the token is invalid/expired.
    """
    return {"valid": True, "username": current_admin}
