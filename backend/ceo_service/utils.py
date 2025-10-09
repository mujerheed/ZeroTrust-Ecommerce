"""
Utility functions for CEO service.
"""

import jwt
import os
from datetime import datetime
from typing import Dict, Any, Optional

SECRET_KEY = os.getenv("JWT_SECRET", "temporary_dev_secret")

def format_response(status: str, message: str, data: Any = None) -> Dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }

def verify_ceo_token(token: str) -> Optional[str]:
    """Validate CEO JWT token and return user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") != "CEO":
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
