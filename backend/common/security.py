"""
JWT utilities, rate limiting, and HTTP errors.
"""

import time
import jwt
from fastapi import HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS
from .config import settings
from threading import Lock

# JWT handling
def create_jwt(subject: str, role: str, expires_minutes: int = 60) -> str:
    """
    Create JWT token with configurable expiration.
    Default: 60 minutes for security (auto-logout after 1 hour of inactivity).
    """
    payload = {
        "sub": subject,
        "role": role,
        "exp": time.time() + expires_minutes * 60
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> dict:
    """
    Decode and validate JWT token.
    Automatically checks expiration (60-minute session timeout).
    
    Raises:
        HTTPException: If token is invalid or expired (401 Unauthorized)
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Session expired. Please log in again for security."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication token"
        )

# Simple in-memory rate limiter
_rate_limits = {}
_rate_lock = Lock()

def rate_limit(request: Request, key: str, limit: int, period_seconds: int):
    identifier = f"{key}:{request.client.host}"
    now = int(time.time())
    window = now // period_seconds

    with _rate_lock:
        count = _rate_limits.get((identifier, window), 0)
        if count >= limit:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )
        _rate_limits[(identifier, window)] = count + 1
