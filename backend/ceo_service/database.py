"""
DynamoDB operations for CEO service.

This module handles all database operations for CEO service including:
- CEO account creation and retrieval
- Vendor management (onboarding, listing, deletion)
- Order queries for CEO dashboard
- Approval request management
- Multi-CEO tenancy enforcement
"""
import time
import secrets
import uuid
from boto3.dynamodb.conditions import Attr, Key
from common.config import settings
from common.db_connection import dynamodb
from typing import Dict, Any, List, Optional

USERS_TABLE = dynamodb.Table(settings.USERS_TABLE)
ORDERS_TABLE = dynamodb.Table(settings.ORDERS_TABLE)
AUDIT_LOGS_TABLE = dynamodb.Table(settings.AUDIT_LOGS_TABLE)
CEO_CONFIG_TABLE = dynamodb.Table(settings.CEO_CONFIG_TABLE)

# Reuse unified OTP table via auth_service
from auth_service.database import save_otp, get_otp, delete_otp


# ==================== CEO Management ====================

def generate_ceo_id() -> str:
    """
    Generate unique CEO identifier.
    Format: ceo_<timestamp>_<uuid>
    """
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"ceo_{timestamp}_{unique_id}"


def create_ceo(name: str, email: str, phone: str, company_name: str = None) -> Dict[str, Any]:
    """
    Create a new CEO account in Users table (OTP-based auth - Zero Trust).
    
    Args:
        name: CEO full name
        email: CEO email (unique identifier)
        phone: CEO phone number (Nigerian format)
        company_name: Optional company/business name
    
    Returns:
        Created CEO record with ceo_id
    """
    ceo_id = generate_ceo_id()
    
    ceo_record = {
        "user_id": ceo_id,
        "ceo_id": ceo_id,  # Self-reference for tenancy queries
        "role": "CEO",
        "name": name,
        "email": email.lower(),
        "phone": phone,
        "company_name": company_name or f"{name}'s Business",
        "verified": False,  # Will be verified via OTP
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    
    USERS_TABLE.put_item(Item=ceo_record)
    return ceo_record


def get_ceo_by_id(ceo_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve CEO record by ceo_id.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        CEO record or None if not found or not a CEO
    """
    resp = USERS_TABLE.get_item(Key={"user_id": ceo_id})
    item = resp.get("Item")
    
    if item and item.get("role") == "CEO":
        return item
    return None


def get_ceo_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve CEO record by email address.
    Uses scan (consider adding GSI for production).
    
    Args:
        email: CEO email address
    
    Returns:
        CEO record or None if not found
    """
    resp = USERS_TABLE.scan(
        FilterExpression=Attr('email').eq(email.lower()) & Attr('role').eq('CEO')
    )
    
    items = resp.get("Items", [])
    return items[0] if items else None


def get_ceo_by_phone_id(whatsapp_phone_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve CEO record by WhatsApp Business Phone Number ID.
    
    This maps a WhatsApp Business Phone Number (from webhook metadata) to the CEO
    who owns that business account. Used for multi-tenancy routing.
    
    Args:
        whatsapp_phone_id: WhatsApp Business Phone Number ID from Meta
    
    Returns:
        CEO record or None if not found
    """
    resp = USERS_TABLE.scan(
        FilterExpression=Attr('role').eq('CEO') & Attr('whatsapp_phone_id').eq(whatsapp_phone_id)
    )
    
    items = resp.get("Items", [])
    return items[0] if items else None


def get_ceo_by_page_id(instagram_page_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve CEO record by Instagram-connected Facebook Page ID.
    
    This maps an Instagram Page ID (from webhook metadata) to the CEO
    who owns that Instagram business account. Used for multi-tenancy routing.
    
    Args:
        instagram_page_id: Instagram Page ID from Meta
    
    Returns:
        CEO record or None if not found
    """
    resp = USERS_TABLE.scan(
        FilterExpression=Attr('role').eq('CEO') & Attr('instagram_page_id').eq(instagram_page_id)
    )
    
    items = resp.get("Items", [])
    return items[0] if items else None


def update_ceo(ceo_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update CEO record with partial updates.
    
    Args:
        ceo_id: CEO identifier
        updates: Fields to update (e.g., {"company_name": "...", "phone": "..."})
    
    Returns:
        Updated CEO record
    """
    update_expr_parts = []
    expr_attr_values = {}
    expr_attr_names = {}
    
    for key, value in updates.items():
        placeholder = f"#{key}"
        value_placeholder = f":{key}"
        update_expr_parts.append(f"{placeholder} = {value_placeholder}")
        expr_attr_names[placeholder] = key
        expr_attr_values[value_placeholder] = value
    
    # Always update timestamp
    update_expr_parts.append("#updated_at = :updated_at")
    expr_attr_names["#updated_at"] = "updated_at"
    expr_attr_values[":updated_at"] = int(time.time())
    
    update_expr = "SET " + ", ".join(update_expr_parts)
    
    resp = USERS_TABLE.update_item(
        Key={"user_id": ceo_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW"
    )
    
    return resp.get("Attributes", {})



# ==================== Vendor Management ====================

def generate_vendor_id() -> str:
    """
    Generate unique vendor identifier.
    Format: vendor_<timestamp>_<uuid>
    """
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"vendor_{timestamp}_{unique_id}"


def create_vendor(vendor_data: Dict[str, Any]) -> str:
    """
    Create a new vendor account (onboarded by CEO).
    
    Args:
        vendor_data: Vendor information including name, email, phone, ceo_id, created_by
    
    Returns:
        vendor_id of created vendor
    """
    if "vendor_id" not in vendor_data:
        vendor_data["vendor_id"] = generate_vendor_id()
        vendor_data["user_id"] = vendor_data["vendor_id"]
    
    # Ensure required fields
    vendor_data["role"] = "Vendor"
    vendor_data["created_at"] = vendor_data.get("created_at", int(time.time()))
    vendor_data["updated_at"] = int(time.time())
    
    USERS_TABLE.put_item(Item=vendor_data)
    return vendor_data["vendor_id"]


def get_vendor_by_id(vendor_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single vendor by vendor_id.
    
    Args:
        vendor_id: Vendor identifier
    
    Returns:
        Vendor record or None if not found or not a vendor
    """
    resp = USERS_TABLE.get_item(Key={"user_id": vendor_id})
    item = resp.get("Item")
    return item if item and item.get("role") == "Vendor" else None


def get_all_vendors_for_ceo(ceo_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all vendors managed by a specific CEO (multi-tenancy).
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        List of vendor records belonging to this CEO
    """
    resp = USERS_TABLE.scan(
        FilterExpression=Attr('role').eq('Vendor') & Attr('ceo_id').eq(ceo_id)
    )
    return resp.get("Items", [])


def get_all_vendors() -> List[Dict[str, Any]]:
    """
    Retrieve all vendor accounts (admin use - not tenant-scoped).
    
    Returns:
        List of all vendor records
    """
    resp = USERS_TABLE.scan(
        FilterExpression=Attr('role').eq('Vendor')
    )
    return resp.get("Items", [])


def delete_vendor(vendor_id: str):
    """
    Remove a vendor account.
    
    Args:
        vendor_id: Vendor identifier to delete
    """
    USERS_TABLE.delete_item(Key={"user_id": vendor_id})


# ==================== Order Queries for CEO Dashboard ====================

def get_orders_for_ceo(ceo_id: str, status: str = None, vendor_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve all orders belonging to a CEO's vendors (multi-tenancy).
    
    Args:
        ceo_id: CEO identifier
        status: Optional order status filter (pending/confirmed/paid/completed/cancelled)
        vendor_id: Optional vendor ID filter
        limit: Maximum number of orders to return
    
    Returns:
        List of order records
    """
    # Build filter expression using Attr() conditions
    filter_expr = Attr('ceo_id').eq(ceo_id)
    
    if status:
        filter_expr = filter_expr & Attr('order_status').eq(status)
    
    if vendor_id:
        filter_expr = filter_expr & Attr('vendor_id').eq(vendor_id)
    
    resp = ORDERS_TABLE.scan(
        FilterExpression=filter_expr,
        Limit=limit
    )
    
    return resp.get("Items", [])



def get_flagged_orders_for_ceo(ceo_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all flagged orders for a CEO's review.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        List of flagged order records
    """
    resp = ORDERS_TABLE.scan(
        FilterExpression=Attr('ceo_id').eq(ceo_id) & Attr('order_status').eq('flagged')
    )
    return resp.get("Items", [])


def get_high_value_orders_for_ceo(ceo_id: str, threshold: float = 1000000) -> List[Dict[str, Any]]:
    """
    Retrieve high-value orders (≥ ₦1,000,000) for CEO approval.
    
    Args:
        ceo_id: CEO identifier
        threshold: Minimum order value (default: ₦1,000,000)
    
    Returns:
        List of high-value order records
    """
    resp = ORDERS_TABLE.scan(
        FilterExpression=Attr('ceo_id').eq(ceo_id) & Attr('total_amount').gte(threshold)
    )
    return resp.get("Items", [])


def get_ceo_dashboard_stats(ceo_id: str) -> Dict[str, Any]:
    """
    Calculate aggregate statistics for CEO dashboard.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        Dictionary with metrics:
        - total_vendors: Number of vendors
        - total_orders: Total order count
        - total_revenue: Sum of completed orders
        - pending_approvals: Count of flagged/high-value orders
        - orders_by_status: Breakdown by status
    """
    # Get all orders for this CEO
    all_orders = get_orders_for_ceo(ceo_id, limit=1000)
    
    # Calculate metrics
    total_orders = len(all_orders)
    total_revenue = sum(
        order.get("total_amount", 0) 
        for order in all_orders 
        if order.get("order_status") in ["completed", "paid"]
    )
    
    # Count by status
    orders_by_status = {}
    for order in all_orders:
        status = order.get("order_status", "unknown")
        orders_by_status[status] = orders_by_status.get(status, 0) + 1
    
    # Pending approvals (flagged + high-value pending)
    flagged_count = orders_by_status.get("flagged", 0)
    high_value_pending = sum(
        1 for order in all_orders 
        if order.get("total_amount", 0) >= 1000000 and order.get("order_status") == "pending"
    )
    pending_approvals = flagged_count + high_value_pending
    
    # Get vendor count
    vendors = get_all_vendors_for_ceo(ceo_id)
    total_vendors = len(vendors)
    
    return {
        "total_vendors": total_vendors,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_approvals": pending_approvals,
        "orders_by_status": orders_by_status
    }


# ==================== Approval Requests ====================

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single order by order_id.
    
    Args:
        order_id: Order identifier
    
    Returns:
        Order record or None if not found
    """
    resp = ORDERS_TABLE.get_item(Key={"order_id": order_id})
    return resp.get("Item")


def update_order_status(order_id: str, new_status: str, approved_by: str = None, notes: str = None):
    """
    Update order status (CEO approval or decline for flagged/high-value orders).
    
    Args:
        order_id: Order identifier
        new_status: New order status (approved/declined/etc.)
        approved_by: CEO user_id who approved/declined
        notes: Optional approval/decline notes
    """
    update_expr = "SET order_status = :s, updated_at = :t"
    expr_values = {
        ":s": new_status,
        ":t": int(time.time())
    }
    
    if approved_by:
        update_expr += ", approved_by = :a"
        expr_values[":a"] = approved_by
    
    if notes:
        update_expr += ", approval_notes = :n"
        expr_values[":n"] = notes
    
    ORDERS_TABLE.update_item(
        Key={"order_id": order_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values
    )



# ==================== Audit Logs ====================

def get_audit_logs(ceo_id: str = None, user_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch recent audit log entries.
    
    Args:
        ceo_id: Optional CEO identifier to filter logs (multi-tenancy)
        user_id: Optional user identifier to filter logs
        limit: Maximum number of logs to return
    
    Returns:
        List of audit log entries
    """
    # Build filter expression
    filter_expr = None
    
    if ceo_id and user_id:
        filter_expr = Attr('ceo_id').eq(ceo_id) & Attr('user_id').eq(user_id)
    elif ceo_id:
        filter_expr = Attr('ceo_id').eq(ceo_id)
    elif user_id:
        filter_expr = Attr('user_id').eq(user_id)
    
    if filter_expr:
        resp = AUDIT_LOGS_TABLE.scan(
            FilterExpression=filter_expr,
            Limit=limit
        )
    else:
        resp = AUDIT_LOGS_TABLE.scan(Limit=limit)
    
    return resp.get("Items", [])


def write_audit_log(ceo_id: str, action: str, user_id: str, details: Dict[str, Any] = None):
    """
    Write an audit log entry for CEO actions.
    
    Args:
        ceo_id: CEO identifier
        action: Action performed (e.g., "vendor_created", "order_approved")
        user_id: User who performed the action
        details: Additional metadata
    """
    log_entry = {
        "log_id": f"{ceo_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}",
        "timestamp": int(time.time()),
        "ceo_id": ceo_id,
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    
    AUDIT_LOGS_TABLE.put_item(Item=log_entry)


# ==================== User Queries ====================

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user (buyer/vendor/CEO) by user_id.
    
    Args:
        user_id: User identifier
    
    Returns:
        User record or None if not found
    """
    resp = USERS_TABLE.get_item(Key={"user_id": user_id})
    return resp.get("Item")


# ==================== CEO Chatbot Configuration ====================

def save_chatbot_config(
    ceo_id: str,
    greeting: str = None,
    tone: str = None,
    **additional_settings
) -> Dict[str, Any]:
    """
    Save or update chatbot configuration for CEO.
    
    Args:
        ceo_id: CEO identifier
        greeting: Custom chatbot greeting message
        tone: Chatbot tone/personality (e.g., "friendly", "professional")
        **additional_settings: Any other chatbot preferences
    
    Returns:
        Updated config record
    """
    config_record = {
        "ceo_id": ceo_id,
        "greeting": greeting or "Welcome to our business! How can I help you today?",
        "tone": tone or "friendly and professional",
        "updated_at": int(time.time()),
    }
    
    # Add any additional settings
    config_record.update(additional_settings)
    
    CEO_CONFIG_TABLE.put_item(Item=config_record)
    return config_record


def get_chatbot_config(ceo_id: str) -> Dict[str, Any]:
    """
    Retrieve chatbot configuration for CEO.
    Returns default config if not customized.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        Chatbot config with greeting, tone, etc.
    """
    resp = CEO_CONFIG_TABLE.get_item(Key={"ceo_id": ceo_id})
    
    if resp.get("Item"):
        return resp["Item"]
    
    # Return default configuration
    return {
        "ceo_id": ceo_id,
        "greeting": "Welcome to our business! How can I help you today?",
        "tone": "friendly and professional",
        "updated_at": None,
    }
