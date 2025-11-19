"""
Utility functions for CEO service.

Provides:
- Response formatting
- JWT token verification
- Data validation helpers
- Masking/privacy functions
"""

from datetime import datetime
from typing import Dict, Any, Optional
from common.security import decode_jwt
from common.logger import logger


def format_response(status: str, message: str, data: Any = None) -> Dict[str, Any]:
    """
    Format consistent API response.
    
    Args:
        status: Response status (success/error)
        message: Human-readable message
        data: Response payload
    
    Returns:
        Formatted response dictionary
    """
    return {
        "status": status,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }


def verify_ceo_token(token: str) -> Optional[str]:
    """
    Validate CEO JWT token and return ceo_id.
    
    Args:
        token: JWT token string
    
    Returns:
        ceo_id if valid and role=CEO, None otherwise
    """
    try:
        payload = decode_jwt(token)
        
        # Verify role is CEO
        if payload.get("role") != "CEO":
            logger.warning("Token verification failed - not CEO role", extra={
                "role": payload.get("role")
            })
            return None
        
        ceo_id = payload.get("sub")
        if not ceo_id:
            logger.warning("Token verification failed - no subject")
            return None
        
        return ceo_id
    
    except Exception as e:
        logger.warning("Token verification failed", extra={"error": str(e)})
        return None


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address
    
    Returns:
        True if valid format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_nigerian_phone(phone: str) -> bool:
    """
    Validate Nigerian phone number format.
    
    Accepts:
    - +234XXXXXXXXXX
    - 234XXXXXXXXXX
    - 0XXXXXXXXXX
    
    Args:
        phone: Phone number string
    
    Returns:
        True if valid Nigerian phone format
    """
    import re
    
    patterns = [
        r'^\+234[0-9]{10}$',  # +234XXXXXXXXXX
        r'^234[0-9]{10}$',     # 234XXXXXXXXXX
        r'^0[0-9]{10}$'        # 0XXXXXXXXXX
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)


def mask_email(email: str) -> str:
    """
    Mask email for privacy (keep first 2 chars + domain).
    
    Args:
        email: Email address
    
    Returns:
        Masked email (e.g., "jo***@example.com")
    """
    if "@" not in email:
        return "***"
    
    local, domain = email.split("@", 1)
    
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[:2] + "***"
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number (show last 4 digits only).
    
    Args:
        phone: Phone number
    
    Returns:
        Masked phone (e.g., "***5678")
    """
    if len(phone) <= 4:
        return "***"
    
    return "***" + phone[-4:]


def format_currency(amount: float, currency: str = "₦") -> str:
    """
    Format amount as currency (Nigerian Naira default).
    
    Args:
        amount: Amount to format
        currency: Currency symbol
    
    Returns:
        Formatted currency string (e.g., "₦1,500,000.00")
    """
    return f"{currency}{amount:,.2f}"
