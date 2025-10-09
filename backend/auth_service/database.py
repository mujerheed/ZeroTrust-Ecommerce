"""
DynamoDB integration for auth_service.
"""

import os
import time
import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Table names from environment (set by SAM/CloudFormation)
USERS_TABLE     = os.getenv("USERS_TABLE")
OTPS_TABLE      = os.getenv("OTPS_TABLE")
AUDIT_LOGS_TABLE = os.getenv("AUDIT_LOGS_TABLE")

def get_user(user_id: str) -> dict:
    """
    Retrieve a user record by user_id.
    """
    table = dynamodb.Table(USERS_TABLE)
    resp  = table.get_item(Key={"user_id": user_id})
    return resp.get("Item")

def save_otp(user_id: str, otp_code: str, role: str, ttl_seconds: int):
    """
    Store an OTP with TTL for a given user.
    """
    table = dynamodb.Table(OTPS_TABLE)
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
    table = dynamodb.Table(OTPS_TABLE)
    resp  = table.get_item(Key={"user_id": user_id})
    return resp.get("Item")

def delete_otp(user_id: str):
    """
    Delete a used or expired OTP record.
    """
    table = dynamodb.Table(OTPS_TABLE)
    table.delete_item(Key={"user_id": user_id})

def log_event(user_id: str, action: str, status: str, message: str = None, meta: dict = None):
    """
    Write an audit log entry.
    """
    if not AUDIT_LOGS_TABLE:
        return
    table = dynamodb.Table(AUDIT_LOGS_TABLE)
    table.put_item(Item={
        "log_id": f"{user_id}-{int(time.time())}",
        "timestamp": int(time.time()),
        "user_id": user_id,
        "action": action,
        "status": status,
        "message": message or "",
        "meta": meta or {}
    })

