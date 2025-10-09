"""
Database operations for Vendor Service.
This will later use boto3 DynamoDB client.
"""

# Placeholder in-memory storage
_orders = {}
_receipts = {}

def save_order(order_id: str, order_data: dict):
    """
    Persist new vendor order.
    """
    _orders[order_id] = order_data

def get_order(order_id: str) -> dict:
    """
    Retrieve order details by ID.
    """
    return _orders.get(order_id)

def save_receipt(order_id: str, receipt_url: str):
    """
    Store receipt URL linked to an order.
    """
    _receipts[order_id] = receipt_url

def get_receipt(order_id: str) -> str:
    """
    Retrieve stored receipt URL.
    """
    return _receipts.get(order_id)
