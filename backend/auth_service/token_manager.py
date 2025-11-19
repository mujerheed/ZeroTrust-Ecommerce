"""
JWT token creation and validation with multi-tenant isolation.

This module provides:
- Role-based JWT creation with ceo_id for multi-tenancy
- Role-specific token expiry (Buyer: 10min, Vendor/CEO: 30min)
- Token revocation tracking via unique jti (JWT ID)
- Integration with AWS Secrets Manager for JWT secret
"""

import jwt
import time
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from common.config import settings
from common.logger import logger

ALGORITHM = "HS256"

# Role-based token expiry
TOKEN_EXPIRY_MINUTES = {
    "BUYER": 10,    # Short-lived for chat-based authentication
    "VENDOR": 30,   # Dashboard session
    "CEO": 30       # Dashboard session
}


def create_jwt(user_id: str, role: str, ceo_id: Optional[str] = None) -> str:
    """
    Create a JWT token for a user with role-based expiry.
    
    Args:
        user_id: Unique identifier for the user (buyer_id, vendor_id, or ceo_id)
        role: User role ("BUYER", "VENDOR", or "CEO")
        ceo_id: CEO identifier for multi-tenancy (optional for CEO role)
    
    Returns:
        JWT token string
    
    Raises:
        ValueError: If role is invalid or required parameters are missing
    """
    if role not in TOKEN_EXPIRY_MINUTES:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(TOKEN_EXPIRY_MINUTES.keys())}")
    
    # Generate unique JWT ID for token revocation tracking
    jti = secrets.token_urlsafe(16)
    
    # Calculate expiry time
    expiry_minutes = TOKEN_EXPIRY_MINUTES[role]
    exp_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    # Build payload
    payload = {
        "sub": user_id,
        "role": role,
        "jti": jti,
        "iat": datetime.utcnow(),
        "exp": exp_time
    }
    
    # Add ceo_id for multi-tenancy
    if role != "CEO" and ceo_id:
        payload["ceo_id"] = ceo_id
    elif role == "CEO":
        payload["ceo_id"] = user_id
    
    try:
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)
        logger.info(f"JWT created for user {user_id} with role {role}")
        return token
    except Exception as e:
        logger.error(f"Failed to create JWT: {str(e)}")
        raise


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        logger.info(f"JWT verified for user {payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed: token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying JWT: {str(e)}")
        return None
