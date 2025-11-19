"""
Business logic for order operations.

Orchestrates order creation, status updates, and buyer notifications.
"""

from typing import Dict, Any, List, Optional
from common.logger import logger
from .database import (
    create_order as db_create_order,
    get_order as db_get_order,
    update_order_status as db_update_order_status,
    list_vendor_orders as db_list_vendor_orders,
    list_buyer_orders as db_list_buyer_orders,
    add_receipt_to_order as db_add_receipt_to_order
)
from .utils import (
    validate_order_items,
    calculate_total,
    validate_buyer_id,
    validate_order_status,
    format_order_for_buyer
)
from auth_service.database import get_buyer_by_id, get_user
from integrations.whatsapp_api import whatsapp_api
from integrations.instagram_api import instagram_api


async def create_order(
    vendor_id: str,
    ceo_id: str,
    buyer_id: str,
    items: List[Dict[str, Any]],
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new order and notify the buyer.
    
    Workflow:
    1. Validate inputs (buyer exists, items valid)
    2. Calculate total amount
    3. Create order in DynamoDB
    4. Send notification to buyer via WhatsApp/Instagram
    5. Return order details
    
    Args:
        vendor_id (str): Vendor creating the order
        ceo_id (str): CEO who owns this business
        buyer_id (str): Buyer for this order (wa_xxx or ig_xxx)
        items (List[Dict]): Order items with name, quantity, price
        notes (str, optional): Additional notes
    
    Returns:
        Dict[str, Any]: Created order with notification status
    
    Raises:
        ValueError: If validation fails
        Exception: If order creation fails
    """
    try:
        # Step 1: Validate buyer exists
        validate_buyer_id(buyer_id)
        buyer = get_buyer_by_id(buyer_id)
        
        if not buyer:
            raise ValueError(f"Buyer not found: {buyer_id}")
        
        # Verify buyer belongs to this CEO (multi-tenancy)
        if buyer.get("ceo_id") != ceo_id:
            raise ValueError("Buyer does not belong to this business")
        
        # Step 2: Validate items and calculate total
        validate_order_items(items)
        total_amount = calculate_total(items)
        
        # Step 3: Create order in database
        order = db_create_order(
            vendor_id=vendor_id,
            buyer_id=buyer_id,
            ceo_id=ceo_id,
            items=items,
            total_amount=total_amount,
            currency="NGN",
            notes=notes
        )
        
        logger.info(f"Order created: {order['order_id']} for buyer {buyer_id}")
        
        # Step 4: Send notification to buyer
        notification_sent = await notify_buyer_new_order(buyer, order)
        
        # Add notification status to response
        order["notification_sent"] = notification_sent
        
        return order
        
    except ValueError as ve:
        logger.warning(f"Order validation failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise Exception(f"Failed to create order: {str(e)}")


async def notify_buyer_new_order(buyer: Dict[str, Any], order: Dict[str, Any]) -> bool:
    """
    Send order notification to buyer via their registered platform.
    
    Args:
        buyer (Dict): Buyer record with platform info
        order (Dict): Order record
    
    Returns:
        bool: True if notification sent successfully
    """
    try:
        platform = buyer.get("platform", "").lower()
        buyer_id = buyer.get("user_id")
        
        # Format order details for messaging
        message = format_order_for_buyer(order)
        
        # Send via appropriate platform
        if platform == "whatsapp":
            phone = buyer.get("phone")
            if not phone:
                logger.warning(f"No phone number for WhatsApp buyer {buyer_id}")
                return False
            
            await whatsapp_api.send_message(
                to=phone,
                message=message
            )
            logger.info(f"Order notification sent via WhatsApp to {buyer_id}")
            return True
            
        elif platform == "instagram":
            psid = buyer.get("meta", {}).get("psid")
            if not psid:
                logger.warning(f"No PSID for Instagram buyer {buyer_id}")
                return False
            
            await instagram_api.send_message(
                recipient_id=psid,
                message=message
            )
            logger.info(f"Order notification sent via Instagram to {buyer_id}")
            return True
            
        else:
            logger.warning(f"Unknown platform for buyer {buyer_id}: {platform}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send order notification: {str(e)}")
        return False


async def confirm_order(order_id: str, buyer_id: str) -> Dict[str, Any]:
    """
    Buyer confirms an order (status: pending → confirmed).
    
    Args:
        order_id (str): Order identifier
        buyer_id (str): Buyer confirming the order
    
    Returns:
        Dict[str, Any]: Updated order record
    
    Raises:
        ValueError: If order not found or buyer mismatch
    """
    try:
        # Retrieve order
        order = db_get_order(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        # Verify buyer owns this order
        if order.get("buyer_id") != buyer_id:
            raise ValueError("Order does not belong to this buyer")
        
        # Verify order is in pending status
        if order.get("status") != "pending":
            raise ValueError(f"Order cannot be confirmed in {order.get('status')} status")
        
        # Update status to confirmed
        updated_order = db_update_order_status(
            order_id=order_id,
            new_status="confirmed",
            notes="Confirmed by buyer"
        )
        
        logger.info(f"Order {order_id} confirmed by buyer {buyer_id}")
        
        # TODO: Notify vendor of confirmation
        
        return updated_order
        
    except ValueError as ve:
        logger.warning(f"Order confirmation failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Order confirmation error: {str(e)}")
        raise Exception(f"Failed to confirm order: {str(e)}")


async def cancel_order(order_id: str, buyer_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Buyer cancels an order (status: pending → cancelled).
    
    Args:
        order_id (str): Order identifier
        buyer_id (str): Buyer cancelling the order
        reason (str, optional): Cancellation reason
    
    Returns:
        Dict[str, Any]: Updated order record
    
    Raises:
        ValueError: If order not found or buyer mismatch
    """
    try:
        # Retrieve order
        order = db_get_order(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        # Verify buyer owns this order
        if order.get("buyer_id") != buyer_id:
            raise ValueError("Order does not belong to this buyer")
        
        # Verify order can be cancelled (pending or confirmed only)
        if order.get("status") not in ["pending", "confirmed"]:
            raise ValueError(f"Order cannot be cancelled in {order.get('status')} status")
        
        # Update status to cancelled
        notes = f"Cancelled by buyer. Reason: {reason}" if reason else "Cancelled by buyer"
        updated_order = db_update_order_status(
            order_id=order_id,
            new_status="cancelled",
            notes=notes
        )
        
        logger.info(f"Order {order_id} cancelled by buyer {buyer_id}")
        
        # TODO: Notify vendor of cancellation
        
        return updated_order
        
    except ValueError as ve:
        logger.warning(f"Order cancellation failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Order cancellation error: {str(e)}")
        raise Exception(f"Failed to cancel order: {str(e)}")


def get_order_details(order_id: str, user_id: str, role: str) -> Dict[str, Any]:
    """
    Get order details with authorization check.
    
    Args:
        order_id (str): Order identifier
        user_id (str): User requesting the order (vendor_id or buyer_id)
        role (str): User role (Vendor or Buyer)
    
    Returns:
        Dict[str, Any]: Order record
    
    Raises:
        ValueError: If order not found or unauthorized
    """
    try:
        order = db_get_order(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        # Authorization check
        if role == "Vendor" and order.get("vendor_id") != user_id:
            raise ValueError("Unauthorized: Order does not belong to this vendor")
        elif role == "Buyer" and order.get("buyer_id") != user_id:
            raise ValueError("Unauthorized: Order does not belong to this buyer")
        
        return order
        
    except ValueError as ve:
        logger.warning(f"Order retrieval failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Order retrieval error: {str(e)}")
        raise Exception(f"Failed to retrieve order: {str(e)}")


def list_orders_for_vendor(vendor_id: str, ceo_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all orders for a vendor with optional status filter.
    
    Args:
        vendor_id (str): Vendor identifier
        ceo_id (str): CEO identifier (ensures multi-tenancy)
        status (str, optional): Filter by status
    
    Returns:
        List[Dict[str, Any]]: List of orders
    """
    try:
        if status:
            validate_order_status(status)
        
        orders = db_list_vendor_orders(
            vendor_id=vendor_id,
            ceo_id=ceo_id,
            status_filter=status
        )
        
        logger.info(f"Retrieved {len(orders)} orders for vendor {vendor_id}")
        return orders
        
    except Exception as e:
        logger.error(f"Failed to list vendor orders: {str(e)}")
        return []


def list_orders_for_buyer(buyer_id: str) -> List[Dict[str, Any]]:
    """
    List all orders for a buyer.
    
    Args:
        buyer_id (str): Buyer identifier
    
    Returns:
        List[Dict[str, Any]]: List of orders
    """
    try:
        orders = db_list_buyer_orders(buyer_id=buyer_id)
        logger.info(f"Retrieved {len(orders)} orders for buyer {buyer_id}")
        return orders
        
    except Exception as e:
        logger.error(f"Failed to list buyer orders: {str(e)}")
        return []


async def add_receipt_to_order(
    order_id: str,
    buyer_id: str,
    receipt_url: str
) -> Dict[str, Any]:
    """
    Add payment receipt to order and update status to 'paid'.
    
    Args:
        order_id (str): Order identifier
        buyer_id (str): Buyer uploading the receipt
        receipt_url (str): S3 URL of uploaded receipt
    
    Returns:
        Dict[str, Any]: Updated order record
    
    Raises:
        ValueError: If order not found or buyer mismatch
    """
    try:
        # Retrieve order
        order = db_get_order(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        # Verify buyer owns this order
        if order.get("buyer_id") != buyer_id:
            raise ValueError("Order does not belong to this buyer")
        
        # Verify order is confirmed (can't upload receipt for pending/cancelled orders)
        if order.get("status") != "confirmed":
            raise ValueError(f"Receipt can only be uploaded for confirmed orders (current status: {order.get('status')})")
        
        # Add receipt and update status
        updated_order = db_add_receipt_to_order(
            order_id=order_id,
            receipt_url=receipt_url
        )
        
        logger.info(f"Receipt added to order {order_id} by buyer {buyer_id}")
        
        # TODO: Notify vendor of receipt upload
        
        return updated_order
        
    except ValueError as ve:
        logger.warning(f"Receipt upload failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Receipt upload error: {str(e)}")
        raise Exception(f"Failed to add receipt: {str(e)}")
