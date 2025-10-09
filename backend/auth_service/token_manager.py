"""
JWT creation and decoding.
"""

import os
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET", "temporary_dev_secret")
ALGORITHM  = "HS256"

def create_jwt(user_id: str, role: str, expires_minutes: int = 30) -> str:
    """
    Generate a signed JWT for the authenticated user.
    """
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> str:
    """
    Decode and validate a JWT, returning the user_id.
    """
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data["sub"]
    except jwt.PyJWTError:
        return None
