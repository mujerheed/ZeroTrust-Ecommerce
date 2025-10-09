"""
DynamoDB operations for CEO service.
"""

import os
import time
import boto3
from typing import Dict, Any, List, Optional

dynamodb = boto3.resource('dynamodb')

USERS_TABLE = os.getenv("USERS_TABLE")
ORDERS_TABLE = os.getenv("ORDERS_TABLE")
AUDIT_LOGS_TABLE = os.getenv("AUDIT_LOGS_TABLE")

# Reuse unified OTP table via auth_service
from auth_service.database import save_otp, get_otp, delete_otp

def get_all_vendors() -> List[Dict[str, Any]]:
    """Retrieve all vendor accounts."""
    table = dynamodb.Table(USERS_TABLE)
    resp  = table.scan(
        FilterExpression="role = :role",
        ExpressionAttributeValues={":role": "Vendor"}
    )
    return resp.get("Items", [])

def get_vendor_by_id(vendor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single vendor by user_id."""
    table = dynamodb.Table(USERS_TABLE)
    resp  = table.get_item(Key={"user_id": vendor_id})
    item  = resp.get("Item")
    return item if item and item.get("role") == "Vendor" else None

def create_vendor(vendor: Dict[str, Any]) -> str:
    """Create a new vendor account."""
    table = dynamodb.Table(USERS_TABLE)
    table.put_item(Item=vendor)
    return vendor["user_id"]

def delete_vendor(vendor_id: str):
    """Remove a vendor account."""
    table = dynamodb.Table(USERS_TABLE)
    table.delete_item(Key={"user_id": vendor_id})

def get_flagged_transactions() -> List[Dict[str, Any]]:
    """Retrieve all orders flagged by vendors."""
    table = dynamodb.Table(ORDERS_TABLE)
    resp  = table.query(
        IndexName="VendorStatusIndex",
        KeyConditionExpression="order_status = :status",
        ExpressionAttributeValues={":status": "flagged"}
    )
    return resp.get("Items", [])

def update_order_status(order_id: str, new_status: str, ceo_id: str):
    """CEO approval or decline for flagged/high-value orders."""
    table = dynamodb.Table(ORDERS_TABLE)
    table.update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET order_status = :s, approved_by = :c, updated_at = :t",
        ExpressionAttributeValues={
            ":s": new_status,
            ":c": ceo_id,
            ":t": int(time.time())
        }
    )

def get_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch recent audit logs entries."""
    table = dynamodb.Table(AUDIT_LOGS_TABLE)
    resp  = table.scan(Limit=limit)
    return resp.get("Items", [])
