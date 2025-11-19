"""
Utility functions for order_service.

Provides validation, formatting, and helper functions.
"""

import re
from typing import Dict, Any, List
from fastapi import HTTPException, Header
from common.logger import logger
from common.security import decode_jwt


def format_response(status: str, message: str, data: Any = None) -> Dict[str, Any]:
    """
    Format API response consistently.
    
    Args:
        status (str): Response status ('success' or 'error')
        message (str): Human-readable message
        data (Any, optional): Response data
    
    Returns:
        Dict[str, Any]: Formatted response
    """
    response = {
        "status": status,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def verify_vendor_token(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    Verify vendor JWT token from Authorization header.
    
    Args:
        authorization (str): Authorization header value
    
    Returns:
        Dict[str, Any]: Decoded token payload with vendor_id and role
    
    Raises:
        HTTPException: If token is missing, invalid, or not a vendor token
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = decode_jwt(token)
        
        # Verify role is Vendor
        if payload.get("role") != "Vendor":
            logger.warning(f"Invalid role for order creation: {payload.get('role')}")
            raise HTTPException(status_code=403, detail="Vendor access required")
        
        return payload
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def verify_buyer_token(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    Verify buyer JWT token from Authorization header.
    
    Args:
        authorization (str): Authorization header value
    
    Returns:
        Dict[str, Any]: Decoded token payload with buyer_id and role
    
    Raises:
        HTTPException: If token is missing, invalid, or not a buyer token
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = decode_jwt(token)
        
        # Verify role is Buyer
        if payload.get("role") != "Buyer":
            logger.warning(f"Invalid role for buyer access: {payload.get('role')}")
            raise HTTPException(status_code=403, detail="Buyer access required")
        
        return payload
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def validate_order_items(items: List[Dict[str, Any]]) -> bool:
    """
    Validate order items structure.
    
    Each item must have: name, quantity, price
    
    Args:
        items (List[Dict]): Order items
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails
    """
    if not items or not isinstance(items, list):
        raise ValueError("Order must contain at least one item")
    
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item {idx} must be a dictionary")
        
        # Required fields
        if "name" not in item or not item["name"]:
            raise ValueError(f"Item {idx}: 'name' is required")
        
        if "quantity" not in item or not isinstance(item["quantity"], (int, float)) or item["quantity"] <= 0:
            raise ValueError(f"Item {idx}: 'quantity' must be a positive number")
        
        if "price" not in item or not isinstance(item["price"], (int, float)) or item["price"] < 0:
            raise ValueError(f"Item {idx}: 'price' must be a non-negative number")
    
    return True


def calculate_total(items: List[Dict[str, Any]]) -> float:
    """
    Calculate total amount from order items.
    
    Args:
        items (List[Dict]): Order items with quantity and price
    
    Returns:
        float: Total amount
    """
    total = 0.0
    for item in items:
        total += item["quantity"] * item["price"]
    return round(total, 2)


def validate_buyer_id(buyer_id: str) -> bool:
    """
    Validate buyer ID format (wa_xxx or ig_xxx).
    
    Args:
        buyer_id (str): Buyer identifier
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If format is invalid
    """
    if not buyer_id:
        raise ValueError("Buyer ID is required")
    
    if not (buyer_id.startswith("wa_") or buyer_id.startswith("ig_")):
        raise ValueError("Buyer ID must start with 'wa_' (WhatsApp) or 'ig_' (Instagram)")
    
    return True


def validate_order_status(status: str) -> bool:
    """
    Validate order status value.
    
    Valid statuses: pending, confirmed, paid, completed, cancelled
    
    Args:
        status (str): Order status
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If status is invalid
    """
    valid_statuses = ["pending", "confirmed", "paid", "completed", "cancelled"]
    
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    return True


def format_order_for_buyer(order: Dict[str, Any]) -> str:
    """
    Format order details for buyer notification message.
    
    Args:
        order (Dict): Order record
    
    Returns:
        str: Formatted message for WhatsApp/Instagram
    
    Example:
        >>> format_order_for_buyer({...})
        "🛒 New Order Created!\n\nOrder ID: ord_123\nTotal: ₦10,000.00\n\nItems:\n1. Product A (x2) - ₦5,000 each\n\nPlease reply with 'confirm' to accept or 'cancel' to reject this order."
    """
    order_id = order.get("order_id", "N/A")
    total = order.get("total_amount", 0)
    currency = order.get("currency", "NGN")
    items = order.get("items", [])
    
    # Format currency symbol
    currency_symbol = "₦" if currency == "NGN" else currency
    
    # Build message
    message = f"🛒 *New Order Created!*\n\n"
    message += f"📋 Order ID: `{order_id}`\n"
    message += f"💰 Total: {currency_symbol}{total:,.2f}\n\n"
    
    # Add items
    if items:
        message += "📦 *Items:*\n"
        for idx, item in enumerate(items, 1):
            name = item.get("name", "Unknown")
            quantity = item.get("quantity", 0)
            price = item.get("price", 0)
            message += f"{idx}. {name} (x{quantity}) - {currency_symbol}{price:,.2f} each\n"
    
    # Add instructions
    message += "\n✅ Reply with *'confirm'* to accept this order\n"
    message += "❌ Reply with *'cancel'* to reject this order\n"
    message += "📸 After confirming, upload your payment receipt using *'upload'*"
    
    return message


def format_order_summary(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format order record for API response (mask sensitive data if needed).
    
    Args:
        order (Dict): Order record from database
    
    Returns:
        Dict[str, Any]: Formatted order for API response
    """
    # For now, return as-is. In production, you might mask buyer PII.
    return order


def mask_buyer_id(buyer_id: str) -> str:
    """
    Mask buyer ID for logging (show platform and last 4 chars).
    
    Args:
        buyer_id (str): Buyer identifier (wa_xxx or ig_xxx)
    
    Returns:
        str: Masked buyer ID
    
    Example:
        >>> mask_buyer_id("wa_2348012345678")
        "wa_****5678"
    """
    if not buyer_id or len(buyer_id) < 8:
        return buyer_id
    
    platform = buyer_id[:3]  # wa_ or ig_
    last_four = buyer_id[-4:]
    return f"{platform}****{last_four}"
