"""
DynamoDB operations for vendor_service.
Handles orders, receipts, and vendor-specific data access.
"""

import time
from common.db_connection import dynamodb
from common.config import settings
from common.logger import logger
from typing import List, Dict, Optional


# Table names from environment
USERS_TABLE = dynamodb.Table(settings.USERS_TABLE)
ORDERS_TABLE = dynamodb.Table(settings.ORDERS_TABLE)
RECEIPTS_TABLE = dynamodb.Table(settings.RECEIPTS_TABLE)
AUDIT_LOGS_TABLE = dynamodb.Table(settings.AUDIT_LOGS_TABLE)
VENDOR_PREFERENCES_TABLE = dynamodb.Table(settings.VENDOR_PREFERENCES_TABLE)

def get_vendor(vendor_id: str) -> Optional[Dict]:
    """Get vendor details by vendor_id. Supports multi-role users."""
    table = USERS_TABLE
    response = table.get_item(Key={"user_id": vendor_id})
    vendor = response.get("Item")
    
    if not vendor:
        logger.info("Vendor not found", extra={"vendor_id": vendor_id})
        return None
    
    # Check if user has Vendor role (either in role field or roles array for multi-role support)
    has_vendor_role = (
        vendor.get("role") == "Vendor" or 
        "Vendor" in vendor.get("roles", [])
    )
    
    logger.info("Vendor lookup", extra={
        "vendor_id": vendor_id, 
        "found": has_vendor_role,
        "role": vendor.get("role"),
        "roles": vendor.get("roles", [])
    })

    return vendor if has_vendor_role else None

def get_vendor_assigned_orders(vendor_id: str, status: str = None) -> List[Dict]:
    """Get all orders assigned to a specific vendor."""
    table = ORDERS_TABLE
    
    # Scan with filter (TODO: add VendorIndex GSI for better performance)
    filter_expression = "vendor_id = :vendor_id"
    expression_values = {":vendor_id": vendor_id}
    
    if status:
        filter_expression += " AND order_status = :status"
        expression_values[":status"] = status
    
    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_values
    )
    
    return response.get("Items", [])

def get_order(order_id: str) -> Optional[Dict]:
    """Get specific order details."""
    table = ORDERS_TABLE
    response = table.get_item(Key={"order_id": order_id})
    return response.get("Item")

def update_order_status(order_id: str, new_status: str, vendor_id: str, notes: str = None):
    """Update order status and log the change."""
    table = ORDERS_TABLE
    
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
    table = RECEIPTS_TABLE
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
        
    table = AUDIT_LOGS_TABLE
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

    logger.info("Vendor action logged", extra={
        "vendor_id": vendor_id,
        "action": action,
        "order_id": order_id
    })


def get_vendor_preferences(vendor_id: str) -> Optional[Dict]:
    """Get vendor preferences from DynamoDB."""
    try:
        response = VENDOR_PREFERENCES_TABLE.get_item(Key={"vendor_id": vendor_id})
        preferences = response.get("Item")
        
        logger.info("Vendor preferences lookup", extra={
            "vendor_id": vendor_id,
            "found": preferences is not None
        })
        
        return preferences
    except Exception as e:
        logger.error(f"Error getting vendor preferences: {e}", extra={"vendor_id": vendor_id})
        return None


def save_vendor_preferences(vendor_id: str, preferences: Dict) -> bool:
    """Save vendor preferences to DynamoDB."""
    try:
        item = {
            "vendor_id": vendor_id,
            "updated_at": int(time.time()),
            **preferences
        }
        
        VENDOR_PREFERENCES_TABLE.put_item(Item=item)
        
        logger.info("Vendor preferences saved", extra={
            "vendor_id": vendor_id,
            "preferences": preferences
        })
        
        return True
    except Exception as e:
        logger.error(f"Error saving vendor preferences: {e}", extra={
            "vendor_id": vendor_id
        })
        return False