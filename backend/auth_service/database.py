"""
DynamoDB integration for auth_service.
"""

import time
from common.config import settings
from common.db_connection import dynamodb

# Table names from environment (set by SAM/CloudFormation)
USERS_TABLE_NAME = settings.USERS_TABLE
OTPS_TABLE_NAME = settings.OTPS_TABLE
AUDIT_LOGS_TABLE_NAME = settings.AUDIT_LOGS_TABLE

def get_user(user_id: str) -> dict:
    """
    Retrieve a user record by user_id.
    """
    table = dynamodb.Table(USERS_TABLE_NAME)
    resp  = table.get_item(Key={"user_id": user_id})
    return resp.get("Item")

def get_buyer_by_id(buyer_id: str) -> dict:
    """
    Retrieve a buyer record by buyer_id.
    Alias for get_user() for clarity when working with buyers.
    
    Args:
        buyer_id: Buyer identifier (format: wa_<phone> or ig_<psid>)
    
    Returns:
        Buyer record from Users table, or None if not found
    """
    return get_user(buyer_id)

def create_buyer(buyer_id: str, phone: str, platform: str, ceo_id: str = None, meta: dict = None) -> dict:
    """
    Create a new buyer record in Users table.
    
    Args:
        buyer_id: Unique buyer identifier (format: wa_<phone> or ig_<psid>)
        phone: Buyer phone number (Nigerian format)
        platform: 'whatsapp' or 'instagram'
        ceo_id: CEO who manages this buyer (for multi-tenancy)
        meta: Additional metadata (e.g., Instagram PSID, username)
    
    Returns:
        Created buyer record
    """
    table = dynamodb.Table(USERS_TABLE_NAME)
    buyer_record = {
        "user_id": buyer_id,
        "role": "Buyer",
        "phone": phone,
        "platform": platform,
        "verified": False,  # Set to True after OTP verification
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    
    if ceo_id:
        buyer_record["ceo_id"] = ceo_id
    
    if meta:
        buyer_record["meta"] = meta
    
    table.put_item(Item=buyer_record)
    return buyer_record

def update_user(user_id: str, updates: dict) -> dict:
    """
    Update user record with partial updates.
    
    Args:
        user_id: User identifier
        updates: Dictionary of fields to update (e.g., {"verified": True, "email": "..."})
    
    Returns:
        Updated user record
    """
    table = dynamodb.Table(USERS_TABLE_NAME)
    
    # Build update expression
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
    
    resp = table.update_item(
        Key={"user_id": user_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW"
    )
    
    return resp.get("Attributes", {})

def save_otp(user_id: str, otp_code: str, role: str, ttl_seconds: int):
    """
    Store an OTP with TTL for a given user.
    """
    table = dynamodb.Table(OTPS_TABLE_NAME)
    expires_at = int(time.time()) + ttl_seconds
    table.put_item(Item={
        "user_id": user_id,
        "otp_code": otp_code,
        "role": role,
        "expires_at": expires_at
    })

def get_otp(user_id: str) -> dict:
    """
    Retrieve the OTP record for a user.
    """
    table = dynamodb.Table(OTPS_TABLE_NAME)
    resp  = table.get_item(Key={"user_id": user_id})
    return resp.get("Item")

def delete_otp(user_id: str):
    """
    Delete a used or expired OTP record.
    """
    table = dynamodb.Table(OTPS_TABLE_NAME)
    table.delete_item(Key={"user_id": user_id})

def log_event(user_id: str, action: str, status: str, message: str = None, meta: dict = None):
    """
    Write an audit log entry.
    """
    if not AUDIT_LOGS_TABLE_NAME:
        return
    table = dynamodb.Table(AUDIT_LOGS_TABLE_NAME)
    table.put_item(Item={
        "log_id": f"{user_id}-{int(time.time())}",
        "timestamp": int(time.time()),
        "user_id": user_id,
        "action": action,
        "status": status,
        "message": message or "",
        "meta": meta or {}
    })

