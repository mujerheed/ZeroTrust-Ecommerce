"""
DynamoDB operations for vendor_service.
Handles orders, receipts, and vendor-specific data access.
"""

import os
import time
import boto3
from typing import List, Dict, Optional

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Table names from environment
USERS_TABLE = os.getenv("USERS_TABLE")
ORDERS_TABLE = os.getenv("ORDERS_TABLE", "TrustGuard-Orders")  # Add to CloudFormation
RECEIPTS_TABLE = os.getenv("RECEIPTS_TABLE", "TrustGuard-Receipts")  # Add to CloudFormation
AUDIT_LOGS_TABLE = os.getenv("AUDIT_LOGS_TABLE")

def get_vendor(vendor_id: str) -> Optional[Dict]:
    """Get vendor details by vendor_id."""
    table = dynamodb.Table(USERS_TABLE)
    response = table.get_item(Key={"user_id": vendor_id})
    vendor = response.get("Item")
    return vendor if vendor and vendor.get("role") == "Vendor" else None

def get_vendor_assigned_orders(vendor_id: str, status: str = None) -> List[Dict]:
    """Get all orders assigned to a specific vendor."""
    table = dynamodb.Table(ORDERS_TABLE)
    
    # Query orders assigned to this vendor
    if status:
        response = table.query(
            IndexName="VendorStatusIndex",  # GSI needed in CloudFormation
            KeyConditionExpression="vendor_id = :vendor_id AND order_status = :status",
            ExpressionAttributeValues={
                ":vendor_id": vendor_id,
                ":status": status
            }
        )
    else:
        response = table.query(
            IndexName="VendorIndex",  # GSI needed in CloudFormation
            KeyConditionExpression="vendor_id = :vendor_id",
            ExpressionAttributeValues={":vendor_id": vendor_id}
        )
    
    return response.get("Items", [])

def get_order(order_id: str) -> Optional[Dict]:
    """Get specific order details."""
    table = dynamodb.Table(ORDERS_TABLE)
    response = table.get_item(Key={"order_id": order_id})
    return response.get("Item")

def update_order_status(order_id: str, new_status: str, vendor_id: str, notes: str = None):
    """Update order status and log the change."""
    table = dynamodb.Table(ORDERS_TABLE)
    
    update_expression = "SET order_status = :status, updated_at = :timestamp, updated_by = :vendor"
    expression_values = {
        ":status": new_status,
        ":timestamp": int(time.time()),
        ":vendor": vendor_id
    }
    
    if notes:
        update_expression += ", vendor_notes = :notes"
        expression_values[":notes"] = notes
    
    table.update_item(
        Key={"order_id": order_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )

def get_receipt(order_id: str) -> Optional[Dict]:
    """Get receipt details for an order."""
    table = dynamodb.Table(RECEIPTS_TABLE)
    response = table.get_item(Key={"order_id": order_id})
    return response.get("Item")

def get_vendor_stats(vendor_id: str) -> Dict:
    """Get vendor dashboard statistics."""
    orders = get_vendor_assigned_orders(vendor_id)
    
    stats = {
        "total_orders": len(orders),
        "pending_verification": len([o for o in orders if o.get("order_status") == "pending_receipt"]),
        "verified_orders": len([o for o in orders if o.get("order_status") == "verified"]),
        "flagged_orders": len([o for o in orders if o.get("order_status") == "flagged"]),
        "total_value": sum(float(o.get("amount", 0)) for o in orders),
        "recent_orders": sorted(orders, key=lambda x: x.get("created_at", 0), reverse=True)[:5]
    }
    return stats

def log_vendor_action(vendor_id: str, action: str, order_id: str = None, details: Dict = None):
    """Log vendor actions for audit trail."""
    if not AUDIT_LOGS_TABLE:
        return
        
    table = dynamodb.Table(AUDIT_LOGS_TABLE)
    table.put_item(Item={
        "log_id": f"{vendor_id}-{int(time.time())}",
        "timestamp": int(time.time()),
        "user_id": vendor_id,
        "user_role": "Vendor",
        "action": action,
        "order_id": order_id or "",
        "details": details or {},
        "status": "SUCCESS"
    })
