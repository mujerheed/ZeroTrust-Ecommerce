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
def create_jwt(subject: str, role: str, expires_minutes: int = 30) -> str:
    payload = {
        "sub": subject,
        "role": role,
        "exp": time.time() + expires_minutes * 60
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")

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
