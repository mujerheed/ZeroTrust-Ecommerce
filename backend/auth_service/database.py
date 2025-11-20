"""
DynamoDB integration for auth_service.
"""

import time
from boto3.dynamodb.conditions import Attr
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


def get_user_by_phone(phone: str, role: str = None) -> dict:
    """
    Retrieve a user by phone number.
    Supports multi-role users (e.g., CEO who is also a Vendor).
    
    Args:
        phone: User's phone number
        role: Optional role filter (CEO, Vendor, Buyer)
    
    Returns:
        User record or None if not found
    """
    table = dynamodb.Table(USERS_TABLE_NAME)
    
    # Scan with filter (not ideal for production, but works for MVP)
    # TODO: Add PhoneIndex GSI in CloudFormation for production
    filter_expression = Attr('phone').eq(phone)
    
    response = table.scan(
        FilterExpression=filter_expression
    )
    
    items = response.get("Items", [])
    
    # If no role filter, return first match
    if not role:
        return items[0] if items else None
    
    # Filter by role (supports both 'role' field and 'roles' array)
    for user in items:
        # Check roles array (multi-role support)
        if 'roles' in user and isinstance(user['roles'], list):
            if role in user['roles']:
                return user
        # Check single role field (legacy)
        elif user.get('role') == role:
            return user
    
    return None


def get_user_by_email(email: str, role: str = None) -> dict:
    """
    Retrieve a user by email address.
    Supports multi-role users (e.g., CEO who is also a Vendor).
    
    Args:
        email: User's email address
        role: Optional role filter (CEO, Vendor, Buyer)
    
    Returns:
        User record or None if not found
    """
    table = dynamodb.Table(USERS_TABLE_NAME)
    
    filter_expression = Attr('email').eq(email)
    
    response = table.scan(
        FilterExpression=filter_expression
    )
    
    items = response.get("Items", [])
    
    # If no role filter, return first match
    if not role:
        return items[0] if items else None
    
    # Filter by role (supports both 'role' field and 'roles' array)
    for user in items:
        # Check roles array (multi-role support)
        if 'roles' in user and isinstance(user['roles'], list):
            if role in user['roles']:
                return user
        # Check single role field (legacy)
        elif user.get('role') == role:
            return user
    
    return None

def create_buyer(
    buyer_id: str, 
    phone: str, 
    platform: str, 
    ceo_id: str = None, 
    name: str = None,
    delivery_address: str = None,
    email: str = None,
    meta: dict = None
) -> dict:
    """
    Create a new buyer record in Users table.
    
    Args:
        buyer_id: Unique buyer identifier (format: wa_<phone> or ig_<psid>)
        phone: Buyer phone number (Nigerian format)
        platform: 'whatsapp' or 'instagram'
        ceo_id: CEO who manages this buyer (for multi-tenancy)
        name: Buyer's full name (optional)
        delivery_address: Delivery address (street, city, landmark) (optional)
        email: Buyer's email address (optional, for Instagram users)
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
    
    if name:
        buyer_record["name"] = name
    
    if delivery_address:
        buyer_record["delivery_address"] = delivery_address
    
    if email:
        buyer_record["email"] = email
    
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

def anonymize_buyer_data(buyer_id: str) -> dict:
    """
    Anonymize buyer PII for GDPR/NDPR compliance (data erasure request).
    
    Implements "right to be forgotten" while preserving anonymized transaction metadata
    for forensic/legal requirements (Core Principle #7).
    
    Process:
    1. Replace name with "[REDACTED]"
    2. Replace phone with "[REDACTED]"
    3. Remove delivery_address (if exists)
    4. Remove email (if exists)
    5. Mark account as anonymized
    6. Preserve: user_id, role, platform, ceo_id, order history references
    
    Args:
        buyer_id: Buyer identifier to anonymize
    
    Returns:
        Anonymized buyer record
    
    Raises:
        ValueError: If buyer not found or already anonymized
    """
    table = dynamodb.Table(USERS_TABLE_NAME)
    
    # Get existing buyer record
    buyer = get_buyer_by_id(buyer_id)
    if not buyer:
        raise ValueError(f"Buyer {buyer_id} not found")
    
    if buyer.get("anonymized"):
        raise ValueError(f"Buyer {buyer_id} already anonymized")
    
    # Build anonymization update
    anonymized_data = {
        "name": "[REDACTED]",
        "phone": "[REDACTED]",
        "anonymized": True,
        "anonymized_at": int(time.time()),
        "data_erasure_reason": "User requested data deletion (GDPR/NDPR compliance)"
    }
    
    # Remove optional PII fields
    remove_expr_parts = []
    if "email" in buyer:
        remove_expr_parts.append("#email")
    if "delivery_address" in buyer:
        remove_expr_parts.append("#delivery_address")
    if "meta" in buyer:
        remove_expr_parts.append("#meta")
    
    # Build update expression
    update_expr_parts = []
    expr_attr_values = {}
    expr_attr_names = {}
    
    for key, value in anonymized_data.items():
        placeholder = f"#{key}"
        value_placeholder = f":{key}"
        update_expr_parts.append(f"{placeholder} = {value_placeholder}")
        expr_attr_names[placeholder] = key
        expr_attr_values[value_placeholder] = value
    
    # Always update timestamp
    update_expr_parts.append("#updated_at = :updated_at")
    expr_attr_names["#updated_at"] = "updated_at"
    expr_attr_values[":updated_at"] = int(time.time())
    
    # Combine SET and REMOVE clauses
    update_expr = "SET " + ", ".join(update_expr_parts)
    
    if remove_expr_parts:
        for field in remove_expr_parts:
            expr_attr_names[field] = field.replace("#", "")
        update_expr += " REMOVE " + ", ".join(remove_expr_parts)
    
    # Execute update
    resp = table.update_item(
        Key={"user_id": buyer_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW"
    )
    
    return resp.get("Attributes", {})

