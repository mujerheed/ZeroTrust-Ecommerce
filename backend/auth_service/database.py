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

