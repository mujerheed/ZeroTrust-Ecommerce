"""
Enhanced utility functions for vendor_service.
"""

import jwt
import os
from datetime import datetime
from typing import Dict, Any, Optional

SECRET_KEY = os.getenv("JWT_SECRET", "temporary_dev_secret")

def format_response(status: str, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Standard API response format."""
    return {
        "status": status,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }

def verify_vendor_token(token: str) -> Optional[str]:
    """Verify JWT token and extract vendor_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        # Ensure this is a vendor token
        if role != "Vendor":
            return None
            
        return user_id
    except jwt.PyJWTError:
        return None

def validate_order_status(status: str) -> bool:
    """Validate order status values."""
    valid_statuses = ["pending", "pending_receipt", "verified", "flagged", "cancelled"]
    return status in valid_statuses

def format_currency(amount: float) -> str:
    """Format amount as Nigerian Naira."""
    return f"₦{amount:,.2f}"

def mask_phone_number(phone: str) -> str:
    """Mask phone number for security (show last 4 digits)."""
    if len(phone) > 4:
        return "*" * (len(phone) - 4) + phone[-4:]
    return phone
