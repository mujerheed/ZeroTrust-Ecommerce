"""
DynamoDB operations for negotiation management.

Handles price negotiation between buyers and vendors before order creation.
"""

import time
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from common.config import settings
from common.db_connection import dynamodb
from common.logger import logger


# Table name from environment
NEGOTIATIONS_TABLE_NAME = getattr(settings, 'NEGOTIATIONS_TABLE', 'TrustGuard-Negotiations-dev')


def generate_negotiation_id() -> str:
    """Generate unique negotiation ID."""
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:12]
    return f"neg_{timestamp}_{unique_id}"


def create_negotiation(
    buyer_id: str,
    vendor_id: str,
    ceo_id: str,
    items: List[Dict[str, Any]],
    delivery_address: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new price negotiation request.
    
    Args:
        buyer_id: Buyer requesting quote
        vendor_id: Vendor to provide quote
        ceo_id: CEO for multi-tenancy
        items: List of items with quantities (no prices yet)
        delivery_address: Optional delivery address
        notes: Optional buyer notes/requirements
    
    Returns:
        Dict with negotiation record
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    negotiation_id = generate_negotiation_id()
    now = int(time.time())
    
    # Convert items to Decimal
    decimal_items = []
    for item in items:
        decimal_item = {
            "name": item["name"],
            "quantity": Decimal(str(item["quantity"]))
        }
        if "description" in item:
            decimal_item["description"] = item["description"]
        decimal_items.append(decimal_item)
    
    negotiation = {
        "negotiation_id": negotiation_id,
        "buyer_id": buyer_id,
        "vendor_id": vendor_id,
        "ceo_id": ceo_id,
        "items": decimal_items,
        "status": "pending_quote",  # pending_quote → quoted → counter_offer → accepted/rejected
        "created_at": now,
        "updated_at": now,
    }
    
    if delivery_address:
        negotiation["delivery_address"] = delivery_address
    
    if notes:
        negotiation["notes"] = notes
    
    table.put_item(Item=negotiation)
    logger.info(f"Negotiation created: {negotiation_id} by buyer {buyer_id} with vendor {vendor_id}")
    
    return negotiation


def get_negotiation(negotiation_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a negotiation by ID.
    
    Args:
        negotiation_id: Negotiation identifier
    
    Returns:
        Negotiation record or None
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    
    try:
        response = table.get_item(Key={"negotiation_id": negotiation_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error retrieving negotiation {negotiation_id}: {str(e)}")
        return None


def add_vendor_quote(
    negotiation_id: str,
    vendor_id: str,
    quoted_items: List[Dict[str, Any]],
    total_amount: Decimal,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Vendor provides pricing quote for negotiation.
    
    Args:
        negotiation_id: Negotiation identifier
        vendor_id: Vendor providing quote
        quoted_items: Items with vendor pricing
        total_amount: Total quoted amount
        notes: Optional vendor notes
    
    Returns:
        Updated negotiation record
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    now = int(time.time())
    
    # Convert items to Decimal
    decimal_items = []
    for item in quoted_items:
        decimal_item = {
            "name": item["name"],
            "quantity": Decimal(str(item["quantity"])),
            "unit_price": Decimal(str(item["unit_price"])),
            "subtotal": Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))
        }
        if "description" in item:
            decimal_item["description"] = item["description"]
        decimal_items.append(decimal_item)
    
    update_expression = "SET vendor_quote = :quote, total_quoted = :total, #status = :status, updated_at = :updated"
    expression_values = {
        ":quote": decimal_items,
        ":total": total_amount,
        ":status": "quoted",
        ":updated": now
    }
    
    if notes:
        update_expression += ", vendor_notes = :notes"
        expression_values[":notes"] = notes
    
    response = table.update_item(
        Key={"negotiation_id": negotiation_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=expression_values,
        ReturnValues="ALL_NEW"
    )
    
    logger.info(f"Vendor {vendor_id} added quote to negotiation {negotiation_id}: ₦{total_amount}")
    return response['Attributes']


def add_buyer_counter(
    negotiation_id: str,
    buyer_id: str,
    requested_discount: Optional[Decimal] = None,
    counter_total: Optional[Decimal] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Buyer submits counter-offer or discount request.
    
    Args:
        negotiation_id: Negotiation identifier
        buyer_id: Buyer making counter-offer
        requested_discount: Discount percentage requested
        counter_total: Counter-offer total amount
        notes: Buyer's reasoning/notes
    
    Returns:
        Updated negotiation record
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    now = int(time.time())
    
    update_expression = "SET #status = :status, updated_at = :updated"
    expression_values = {
        ":status": "counter_offer",
        ":updated": now
    }
    
    if requested_discount:
        update_expression += ", requested_discount = :discount"
        expression_values[":discount"] = requested_discount
    
    if counter_total:
        update_expression += ", counter_total = :counter"
        expression_values[":counter"] = counter_total
    
    if notes:
        update_expression += ", buyer_notes = :notes"
        expression_values[":notes"] = notes
    
    response = table.update_item(
        Key={"negotiation_id": negotiation_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=expression_values,
        ReturnValues="ALL_NEW"
    )
    
    logger.info(f"Buyer {buyer_id} submitted counter-offer for negotiation {negotiation_id}")
    return response['Attributes']


def update_negotiation_status(
    negotiation_id: str,
    status: str,
    final_amount: Optional[Decimal] = None
) -> Dict[str, Any]:
    """
    Update negotiation status (accepted/rejected).
    
    Args:
        negotiation_id: Negotiation identifier
        status: New status (accepted, rejected)
        final_amount: Final agreed amount (if accepted)
    
    Returns:
        Updated negotiation record
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    now = int(time.time())
    
    update_expression = "SET #status = :status, updated_at = :updated"
    expression_values = {
        ":status": status,
        ":updated": now
    }
    
    if final_amount and status == "accepted":
        update_expression += ", final_amount = :final"
        expression_values[":final"] = final_amount
    
    response = table.update_item(
        Key={"negotiation_id": negotiation_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=expression_values,
        ReturnValues="ALL_NEW"
    )
    
    logger.info(f"Negotiation {negotiation_id} status updated to: {status}")
    return response['Attributes']


def list_negotiations_by_buyer(buyer_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all negotiations for a buyer.
    
    Args:
        buyer_id: Buyer identifier
        status: Optional status filter
    
    Returns:
        List of negotiation records
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    
    try:
        # Scan with filter (in production, use GSI on buyer_id)
        filter_expression = "buyer_id = :buyer_id"
        expression_values = {":buyer_id": buyer_id}
        
        if status:
            filter_expression += " AND #status = :status"
            expression_values[":status"] = status
        
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeNames={"#status": "status"} if status else {},
            ExpressionAttributeValues=expression_values
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing negotiations for buyer {buyer_id}: {str(e)}")
        return []


def list_negotiations_by_vendor(vendor_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all negotiations for a vendor.
    
    Args:
        vendor_id: Vendor identifier
        status: Optional status filter
    
    Returns:
        List of negotiation records
    """
    table = dynamodb.Table(NEGOTIATIONS_TABLE_NAME)
    
    try:
        # Scan with filter (in production, use GSI on vendor_id)
        filter_expression = "vendor_id = :vendor_id"
        expression_values = {":vendor_id": vendor_id}
        
        if status:
            filter_expression += " AND #status = :status"
            expression_values[":status"] = status
        
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeNames={"#status": "status"} if status else {},
            ExpressionAttributeValues=expression_values
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error listing negotiations for vendor {vendor_id}: {str(e)}")
        return []
