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
from integrations.whatsapp_api import WhatsAppAPI
from integrations.instagram_api import InstagramAPI
from integrations.secrets_helper import get_meta_secrets


async def create_order(
    vendor_id: str,
    ceo_id: str,
    buyer_id: str,
    items: List[Dict[str, Any]],
    notes: Optional[str] = None,
    requires_delivery: bool = False,
    delivery_address: Optional[Dict[str, Any]] = None,
    use_registered_address: bool = True
) -> Dict[str, Any]:
    """
    Create a new order and notify the buyer.
    
    Workflow:
    1. Validate inputs (buyer exists, items valid)
    2. Handle delivery address (use registered or custom)
    3. Calculate total amount
    4. Create order in DynamoDB
    5. Send notification to buyer via WhatsApp/Instagram
    6. Return order details
    
    Args:
        vendor_id (str): Vendor creating the order
        ceo_id (str): CEO who owns this business
        buyer_id (str): Buyer for this order (wa_xxx or ig_xxx)
        items (List[Dict]): Order items with name, quantity, price
        notes (str, optional): Additional notes
        requires_delivery (bool): Whether buyer wants delivery
        delivery_address (Dict, optional): Custom delivery address
        use_registered_address (bool): Use buyer's registered address
    
    Returns:
        Dict[str, Any]: Created order with notification status
    
    Raises:
        ValueError: If validation fails
        Exception: If order creation fails
    """
    try:
        # Step 1: Validate buyer exists
        logger.info(f"Creating order - Vendor: {vendor_id}, Buyer: {buyer_id}, CEO: {ceo_id}, Delivery: {requires_delivery}")
        
        validate_buyer_id(buyer_id)
        buyer = get_buyer_by_id(buyer_id)
        
        if not buyer:
            logger.error(f"Buyer not found: {buyer_id}")
            raise ValueError(f"Buyer not found: {buyer_id}")
        
        logger.info(f"Buyer found: {buyer_id}, platform: {buyer.get('platform')}")
        
        # Verify buyer belongs to this CEO (multi-tenancy)
        if buyer.get("ceo_id") != ceo_id:
            logger.error(f"Multi-tenancy violation - Buyer CEO: {buyer.get('ceo_id')}, Order CEO: {ceo_id}")
            raise ValueError("Buyer does not belong to this business")
        
        # Step 2: Handle delivery address
        final_delivery_address = None
        if requires_delivery:
            if use_registered_address:
                # Use buyer's registered address
                logger.info("Using buyer's registered address for delivery")
                final_delivery_address = {
                    "street": buyer.get("street", ""),
                    "city": buyer.get("city", ""),
                    "state": buyer.get("state", ""),
                    "postal_code": buyer.get("postal_code"),
                    "country": buyer.get("country", "Nigeria"),
                    "phone": buyer.get("phone"),
                    "landmark": buyer.get("landmark")
                }
            elif delivery_address:
                # Use custom delivery address
                logger.info("Using custom delivery address")
                final_delivery_address = delivery_address
            else:
                raise ValueError("Delivery requested but no address provided")
        
        # Step 3: Validate items and calculate total
        logger.info(f"Validating {len(items)} order items")
        validate_order_items(items)
        total_amount = calculate_total(items)
        logger.info(f"Order total calculated: {total_amount} NGN")
        
        # Step 4: Create order in database with delivery info
        logger.info("Creating order in database")
        order = db_create_order(
            vendor_id=vendor_id,
            buyer_id=buyer_id,
            ceo_id=ceo_id,
            items=items,
            total_amount=total_amount,
            currency="NGN",
            notes=notes,
            requires_delivery=requires_delivery,
            delivery_address=final_delivery_address
        )
        
        logger.info(f"Order created: {order['order_id']} for buyer {buyer_id}, Delivery: {requires_delivery}")
        
        # Step 5: Get CEO's bank details for payment instructions
        logger.info(f"Fetching CEO bank details for ceo_id: {ceo_id}")
        ceo = get_user(ceo_id)
        bank_details = ceo.get("bank_details") if ceo else None
        
        if bank_details:
            logger.info(f"Bank details found for CEO {ceo_id}")
            order["payment_details"] = {
                "bank_name": bank_details.get("bank_name"),
                "account_number": bank_details.get("account_number"),
                "account_name": bank_details.get("account_name"),
                "instructions": f"Please make payment to the account above for order {order['order_id']}. Upload receipt after payment."
            }
        else:
            logger.warning(f"No bank details configured for CEO {ceo_id}")
            order["payment_details"] = None
        
        # Step 6: Send notification to buyer
        logger.info("Sending order notification to buyer")
        notification_sent = await notify_buyer_new_order(buyer, order)
        
        if notification_sent:
            logger.info("Order notification sent successfully")
        else:
            logger.warning("Order notification failed to send")
        
        # Add notification status to response
        order["notification_sent"] = notification_sent
        
        return order
        
    except ValueError as ve:
        logger.warning(f"Order validation failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}", exc_info=True)
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
        
        # Fetch Meta credentials from Secrets Manager
        meta_secrets = await get_meta_secrets()
        if not meta_secrets:
            logger.error("Failed to fetch Meta credentials from Secrets Manager")
            return False
        
        # Send via appropriate platform
        if platform == "whatsapp":
            phone = buyer.get("phone")
            if not phone:
                logger.warning(f"No phone number for WhatsApp buyer {buyer_id}")
                return False
            
            # Get WhatsApp credentials
            whatsapp_token = meta_secrets.get("whatsapp_access_token")
            whatsapp_phone_id = meta_secrets.get("whatsapp_phone_number_id")
            
            if not whatsapp_token or not whatsapp_phone_id:
                logger.error(f"WhatsApp credentials not found in Secrets Manager. Token present: {bool(whatsapp_token)}, Phone ID present: {bool(whatsapp_phone_id)}")
                return False
            
            # Initialize WhatsApp API with credentials
            whatsapp_client = WhatsAppAPI(
                access_token=whatsapp_token,
                phone_number_id=whatsapp_phone_id
            )
            
            await whatsapp_client.send_message(
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
            
            # Get Instagram credentials
            instagram_token = meta_secrets.get("instagram_access_token")
            instagram_page_id = meta_secrets.get("instagram_page_id")
            
            if not instagram_token:
                logger.error("Instagram credentials not found in Secrets Manager")
                return False
            
            # Initialize Instagram API with credentials
            instagram_client = InstagramAPI(
                access_token=instagram_token,
                page_id=instagram_page_id
            )
            
            await instagram_client.send_message(
                to=psid,
                message=message
            )
            logger.info(f"Order notification sent via Instagram to {buyer_id}")
            return True
            
        else:
            logger.warning(f"Unknown platform for buyer {buyer_id}: {platform}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send order notification: {str(e)}", exc_info=True)
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


async def update_delivery_address(
    order_id: str,
    buyer_id: str,
    requires_delivery: bool,
    delivery_address: Optional[Dict[str, Any]] = None,
    use_registered_address: bool = False
) -> Dict[str, Any]:
    """
    Update delivery address for an order.
    
    Args:
        order_id (str): Order identifier
        buyer_id (str): Buyer updating delivery info
        requires_delivery (bool): Whether delivery is required
        delivery_address (Dict, optional): Custom delivery address
        use_registered_address (bool): Use buyer's registered address
    
    Returns:
        Dict[str, Any]: Updated order record
    
    Raises:
        ValueError: If validation fails
    """
    try:
        # Retrieve order
        order = db_get_order(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        # Verify buyer owns this order
        if order.get("buyer_id") != buyer_id:
            raise ValueError("Order does not belong to this buyer")
        
        # Can only update delivery for pending/confirmed orders
        if order.get("status") not in ["pending", "confirmed"]:
            raise ValueError(f"Cannot update delivery for {order.get('status')} orders")
        
        # Handle delivery address
        final_delivery_address = None
        if requires_delivery:
            if use_registered_address:
                # Fetch buyer's registered address
                buyer = get_buyer_by_id(buyer_id)
                if not buyer:
                    raise ValueError("Buyer not found")
                
                final_delivery_address = {
                    "street": buyer.get("street", ""),
                    "city": buyer.get("city", ""),
                    "state": buyer.get("state", ""),
                    "postal_code": buyer.get("postal_code"),
                    "country": buyer.get("country", "Nigeria"),
                    "phone": buyer.get("phone"),
                    "landmark": buyer.get("landmark")
                }
                logger.info(f"Using registered address for delivery - Order: {order_id}")
            elif delivery_address:
                final_delivery_address = delivery_address
                logger.info(f"Using custom address for delivery - Order: {order_id}")
            else:
                raise ValueError("Delivery requested but no address provided")
        
        # Update order in database
        from .database import update_delivery_address as db_update_delivery
        updated_order = db_update_delivery(
            order_id=order_id,
            requires_delivery=requires_delivery,
            delivery_address=final_delivery_address
        )
        
        logger.info(f"Delivery address updated for order {order_id}, Requires delivery: {requires_delivery}")
        
        return updated_order
        
    except ValueError as ve:
        logger.warning(f"Delivery address update failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Delivery address update error: {str(e)}")
        raise Exception(f"Failed to update delivery address: {str(e)}")


async def get_order_summary(order_id: str, user_id: str, role: str) -> Dict[str, Any]:
    """
    Get comprehensive order summary with all details.
    
    Returns enriched order data suitable for:
    - Dashboard display
    - PDF generation
    - Email notifications
    - Receipt printing
    
    Args:
        order_id (str): Order identifier
        user_id (str): User requesting summary (vendor_id or buyer_id)
        role (str): User role (Vendor or Buyer)
    
    Returns:
        Dict[str, Any]: Complete order summary with calculated fields
    
    Raises:
        ValueError: If order not found or unauthorized
    """
    try:
        # Get order with authorization check
        order = get_order_details(order_id, user_id, role)
        
        # Calculate item subtotals
        items_with_subtotals = []
        for item in order.get("items", []):
            item_copy = item.copy()
            quantity = item.get("quantity", 0)
            price = item.get("price", 0.0)
            item_copy["subtotal"] = round(quantity * price, 2)
            items_with_subtotals.append(item_copy)
        
        # Build comprehensive summary
        summary = {
            "order_id": order.get("order_id"),
            "status": order.get("status"),
            "created_at": order.get("created_at"),
            "updated_at": order.get("updated_at"),
            "buyer_id": order.get("buyer_id"),
            "vendor_id": order.get("vendor_id"),
            "ceo_id": order.get("ceo_id"),
            "items": items_with_subtotals,
            "total_amount": order.get("total_amount"),
            "currency": order.get("currency", "NGN"),
            "payment_details": order.get("payment_details"),
            "requires_delivery": order.get("requires_delivery", False),
            "delivery_address": order.get("delivery_address"),
            "notes": order.get("notes")
        }
        
        # Add receipt information if available
        if order.get("receipt_id"):
            summary["receipt"] = {
                "receipt_id": order.get("receipt_id"),
                "uploaded_at": order.get("receipt_uploaded_at"),
                "status": order.get("receipt_status", "pending_verification"),
                "s3_key": order.get("receipt_s3_key")
            }
        else:
            summary["receipt"] = None
        
        # Add negotiation info if exists
        if order.get("negotiation_id"):
            summary["negotiation"] = {
                "negotiation_id": order.get("negotiation_id"),
                "original_price": order.get("original_price"),
                "final_price": order.get("total_amount"),
                "discount": order.get("original_price", 0) - order.get("total_amount", 0) if order.get("original_price") else 0
            }
        
        logger.info(f"Order summary generated for {order_id}")
        return summary
        
    except ValueError as ve:
        logger.warning(f"Order summary failed: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Order summary error: {str(e)}")
        raise Exception(f"Failed to generate order summary: {str(e)}")
