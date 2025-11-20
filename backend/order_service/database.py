"""
DynamoDB operations for order_service.

Handles all database interactions for orders:
- Order CRUD operations
- Vendor order queries
- Buyer order queries
- Order status updates
- Multi-CEO data isolation
"""

import time
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from common.config import settings
from common.db_connection import dynamodb
from common.logger import logger

# Table name from environment
ORDERS_TABLE_NAME = settings.ORDERS_TABLE


def generate_order_id() -> str:
    """
    Generate unique order ID with timestamp prefix for sortability.
    
    Format: ord_<timestamp>_<uuid4>
    Example: ord_1700000000_a1b2c3d4
    
    Returns:
        str: Unique order identifier
    """
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"ord_{timestamp}_{unique_id}"


def create_order(
    vendor_id: str,
    buyer_id: str,
    ceo_id: str,
    items: List[Dict[str, Any]],
    total_amount: Decimal,
    currency: str = "NGN",
    notes: Optional[str] = None,
    requires_delivery: bool = False,
    delivery_address: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new order in DynamoDB.
    
    Args:
        vendor_id (str): Vendor creating the order
        buyer_id (str): Buyer for this order (wa_xxx or ig_xxx)
        ceo_id (str): CEO who owns this business (multi-tenancy)
        items (List[Dict]): Order items with name, quantity, price
        total_amount (Decimal): Total order amount in NGN
        currency (str): Currency code (default: NGN)
        notes (str, optional): Additional notes for the order
        requires_delivery (bool): Whether buyer wants delivery
        delivery_address (Dict, optional): Delivery address if required
    
    Returns:
        Dict[str, Any]: Created order record
    
    Example:
        >>> create_order(
        ...     vendor_id="vendor_123",
        ...     buyer_id="wa_2348012345678",
        ...     ceo_id="ceo_456",
        ...     items=[{"name": "Product A", "quantity": 2, "price": 5000}],
        ...     total_amount=Decimal("10000"),
        ...     requires_delivery=True,
        ...     delivery_address={"city": "Lagos", ...}
        ... )
        {
            "order_id": "ord_1700000000_a1b2c3d4",
            "vendor_id": "vendor_123",
            "buyer_id": "wa_2348012345678",
            "ceo_id": "ceo_456",
            "items": [...],
            "total_amount": Decimal("10000"),
            "currency": "NGN",
            "status": "pending",
            "requires_delivery": True,
            "delivery_address": {...},
            "created_at": 1700000000,
            "updated_at": 1700000000
        }
    """
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    order_id = generate_order_id()
    now = int(time.time())
    
    # Convert items to use Decimal for DynamoDB compatibility
    decimal_items = []
    for item in items:
        decimal_item = {
            "name": item["name"],
            "quantity": Decimal(str(item["quantity"])),
            "price": Decimal(str(item["price"]))
        }
        # Preserve optional fields
        if "description" in item:
            decimal_item["description"] = item["description"]
        if "sku" in item:
            decimal_item["sku"] = item["sku"]
        decimal_items.append(decimal_item)
    
    order = {
        "order_id": order_id,
        "vendor_id": vendor_id,
        "buyer_id": buyer_id,
        "ceo_id": ceo_id,
        "items": decimal_items,
        "total_amount": total_amount,
        "currency": currency,
        "status": "pending",  # pending → confirmed → paid → completed (or cancelled)
        "requires_delivery": requires_delivery,
        "created_at": now,
        "updated_at": now,
    }
    
    if notes:
        order["notes"] = notes
    
    if delivery_address:
        order["delivery_address"] = delivery_address
    
    table.put_item(Item=order)
    logger.info(f"Order created: {order_id} by vendor {vendor_id} for buyer {buyer_id}, Delivery: {requires_delivery}")
    
    return order


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an order by order_id.
    
    Args:
        order_id (str): Order identifier
    
    Returns:
        Optional[Dict]: Order record or None if not found
    """
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    
    try:
        response = table.get_item(Key={"order_id": order_id})
        return response.get("Item")
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {str(e)}")
        return None


def update_order_status(
    order_id: str,
    new_status: str,
    receipt_url: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update order status and optionally add receipt URL.
    
    Args:
        order_id (str): Order identifier
        new_status (str): New status (confirmed/paid/completed/cancelled)
        receipt_url (str, optional): S3 URL of payment receipt
        notes (str, optional): Additional notes for this status change
    
    Returns:
        Dict[str, Any]: Updated order record
    """
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    now = int(time.time())
    
    update_expr = "SET #status = :status, #updated_at = :updated_at"
    expr_attr_names = {
        "#status": "status",
        "#updated_at": "updated_at"
    }
    expr_attr_values = {
        ":status": new_status,
        ":updated_at": now
    }
    
    if receipt_url:
        update_expr += ", #receipt_url = :receipt_url"
        expr_attr_names["#receipt_url"] = "receipt_url"
        expr_attr_values[":receipt_url"] = receipt_url
    
    if notes:
        update_expr += ", #notes = :notes"
        expr_attr_names["#notes"] = "notes"
        expr_attr_values[":notes"] = notes
    
    response = table.update_item(
        Key={"order_id": order_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW"
    )
    
    logger.info(f"Order {order_id} status updated: {new_status}")
    return response.get("Attributes", {})


def list_vendor_orders(
    vendor_id: str,
    ceo_id: str,
    status_filter: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    List all orders for a specific vendor, optionally filtered by status.
    
    Args:
        vendor_id (str): Vendor identifier
        ceo_id (str): CEO identifier (ensures multi-tenancy)
        status_filter (str, optional): Filter by status (pending/confirmed/paid/completed/cancelled)
        limit (int): Maximum number of orders to return
    
    Returns:
        List[Dict[str, Any]]: List of order records
    """
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    
    # Query using ByVendorAndCEO GSI
    query_kwargs = {
        "IndexName": "ByVendorAndCEO",
        "KeyConditionExpression": "vendor_id = :vendor_id AND ceo_id = :ceo_id",
        "ExpressionAttributeValues": {
            ":vendor_id": vendor_id,
            ":ceo_id": ceo_id
        },
        "Limit": limit,
        "ScanIndexForward": False  # Most recent first
    }
    
    # Add status filter if provided
    if status_filter:
        query_kwargs["FilterExpression"] = "#status = :status"
        query_kwargs["ExpressionAttributeNames"] = {"#status": "status"}
        query_kwargs["ExpressionAttributeValues"][":status"] = status_filter
    
    try:
        response = table.query(**query_kwargs)
        return response.get("Items", [])
    except Exception as e:
        logger.error(f"Error listing orders for vendor {vendor_id}: {str(e)}")
        return []


def list_buyer_orders(buyer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List all orders for a specific buyer.
    
    Args:
        buyer_id (str): Buyer identifier (wa_xxx or ig_xxx)
        limit (int): Maximum number of orders to return
    
    Returns:
        List[Dict[str, Any]]: List of order records
    
    Note:
        Uses a scan with filter. For production, consider adding a GSI on buyer_id.
    """
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    
    try:
        response = table.scan(
            FilterExpression="buyer_id = :buyer_id",
            ExpressionAttributeValues={":buyer_id": buyer_id},
            Limit=limit
        )
        return response.get("Items", [])
    except Exception as e:
        logger.error(f"Error listing orders for buyer {buyer_id}: {str(e)}")
        return []


def delete_order(order_id: str) -> bool:
    """
    Delete an order (admin/CEO only, typically for data cleanup).
    
    Args:
        order_id (str): Order identifier
    
    Returns:
        bool: True if deleted successfully
    """
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    
    try:
        table.delete_item(Key={"order_id": order_id})
        logger.info(f"Order deleted: {order_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {str(e)}")
        return False


def add_receipt_to_order(order_id: str, receipt_url: str) -> Dict[str, Any]:
    """
    Add receipt URL to order and update status to 'paid'.
    
    Args:
        order_id (str): Order identifier
        receipt_url (str): S3 URL of uploaded receipt
    
    Returns:
        Dict[str, Any]: Updated order record
    """
    return update_order_status(
        order_id=order_id,
        new_status="paid",
        receipt_url=receipt_url,
        notes="Receipt uploaded by buyer"
    )


def update_delivery_address(
    order_id: str,
    requires_delivery: bool,
    delivery_address: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update delivery preferences for an order.
    
    Args:
        order_id (str): Order identifier
        requires_delivery (bool): Whether delivery is required
        delivery_address (Dict, optional): Delivery address details (street, city, state, etc.)
    
    Returns:
        Dict[str, Any]: Updated order record
    
    Raises:
        ValueError: If delivery is required but no address provided
    """
    if requires_delivery and not delivery_address:
        raise ValueError("Delivery address is required when delivery is enabled")
    
    table = dynamodb.Table(ORDERS_TABLE_NAME)
    now = int(time.time())
    
    update_expr = "SET #requires_delivery = :requires_delivery, #updated_at = :updated_at"
    expr_attr_names = {
        "#requires_delivery": "requires_delivery",
        "#updated_at": "updated_at"
    }
    expr_attr_values = {
        ":requires_delivery": requires_delivery,
        ":updated_at": now
    }
    
    if delivery_address:
        update_expr += ", #delivery_address = :delivery_address"
        expr_attr_names["#delivery_address"] = "delivery_address"
        expr_attr_values[":delivery_address"] = delivery_address
    elif not requires_delivery:
        # Remove delivery_address if delivery is disabled
        update_expr += " REMOVE #delivery_address"
        expr_attr_names["#delivery_address"] = "delivery_address"
        # Don't include :delivery_address in values when using REMOVE
    
    response = table.update_item(
        Key={"order_id": order_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues={k: v for k, v in expr_attr_values.items() if not k.startswith(":delivery_address") or delivery_address},
        ReturnValues="ALL_NEW"
    )
    
    updated_order = response["Attributes"]
    logger.info(f"Order {order_id} delivery preferences updated: requires_delivery={requires_delivery}")
    
    return updated_order
