"""
Utility functions for Vendor Service
"""

import re
from datetime import datetime
from typing import Dict, Any

def format_response(status: str, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Standard API response format.
    """
    return {
        "status": status,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }

def validate_order_id(order_id: str) -> bool:
    """
    Ensure order_id follows expected format, e.g., 'order-1234'.
    """
    if not re.match(r'^order-\d+$', order_id):
        raise ValueError("Invalid order_id format")
    return True

def mask_receipt_url(url: str) -> str:
    """
    Optionally mask parts of a receipt URL for privacy.
    """
    return url.replace("https://", "https://***.")
