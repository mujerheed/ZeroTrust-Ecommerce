"""
Business logic for price negotiation between buyers and vendors.

Flow:
1. Buyer requests quote for items with quantities
2. Vendor provides pricing for each item
3. Buyer can accept or counter-offer (request discount)
4. Vendor can accept counter-offer or modify
5. Once accepted, negotiation converts to actual order
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from common.logger import logger
from integrations.whatsapp_api import WhatsAppAPI
from integrations.instagram_api import InstagramAPI
from integrations.secrets_helper import get_meta_secrets
from auth_service.database import get_buyer_by_id, get_user
from .database import (
    create_negotiation as db_create_negotiation,
    get_negotiation as db_get_negotiation,
    add_vendor_quote as db_add_vendor_quote,
    add_buyer_counter as db_add_buyer_counter,
    update_negotiation_status as db_update_negotiation_status,
    list_negotiations_by_buyer,
    list_negotiations_by_vendor
)


async def request_quote(
    buyer_id: str,
    vendor_id: str,
    ceo_id: str,
    items: List[Dict[str, Any]],
    delivery_address: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Buyer requests a price quote from vendor.
    
    Args:
        buyer_id: Buyer requesting quote
        vendor_id: Vendor to provide quote
        ceo_id: CEO for multi-tenancy
        items: Items with quantities (no prices)
        delivery_address: Optional delivery address
        notes: Buyer's requirements/notes
    
    Returns:
        Created negotiation record
    """
    try:
        logger.info(f"Buyer {buyer_id} requesting quote from vendor {vendor_id}")
        
        # Validate buyer
        buyer = get_buyer_by_id(buyer_id)
        if not buyer:
            raise ValueError(f"Buyer not found: {buyer_id}")
        
        # Verify multi-tenancy
        if buyer.get("ceo_id") != ceo_id:
            raise ValueError("Buyer does not belong to this business")
        
        # Validate items
        if not items or len(items) == 0:
            raise ValueError("At least one item required for quote request")
        
        for idx, item in enumerate(items):
            if not item.get("name"):
                raise ValueError(f"Item {idx}: name is required")
            if not item.get("quantity") or item["quantity"] <= 0:
                raise ValueError(f"Item {idx}: quantity must be greater than 0")
        
        # Create negotiation
        negotiation = db_create_negotiation(
            buyer_id=buyer_id,
            vendor_id=vendor_id,
            ceo_id=ceo_id,
            items=items,
            delivery_address=delivery_address,
            notes=notes
        )
        
        # Notify vendor
        vendor = get_user(vendor_id)
        if vendor:
            await notify_vendor_new_quote_request(vendor, buyer, negotiation)
        
        logger.info(f"Quote request created: {negotiation['negotiation_id']}")
        return negotiation
        
    except Exception as e:
        logger.error(f"Quote request failed: {str(e)}", exc_info=True)
        raise


async def vendor_provide_quote(
    negotiation_id: str,
    vendor_id: str,
    quoted_items: List[Dict[str, Any]],
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Vendor provides pricing for quote request.
    
    Args:
        negotiation_id: Negotiation identifier
        vendor_id: Vendor providing quote
        quoted_items: Items with unit_price
        notes: Vendor notes
    
    Returns:
        Updated negotiation record
    """
    try:
        # Get negotiation
        negotiation = db_get_negotiation(negotiation_id)
        if not negotiation:
            raise ValueError(f"Negotiation not found: {negotiation_id}")
        
        # Verify vendor
        if negotiation.get("vendor_id") != vendor_id:
            raise ValueError("Not authorized for this negotiation")
        
        # Verify status
        if negotiation.get("status") != "pending_quote":
            raise ValueError(f"Cannot quote negotiation with status: {negotiation.get('status')}")
        
        # Calculate total
        total_amount = Decimal("0")
        for item in quoted_items:
            quantity = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(item["unit_price"]))
            total_amount += quantity * unit_price
        
        # Update negotiation
        updated = db_add_vendor_quote(
            negotiation_id=negotiation_id,
            vendor_id=vendor_id,
            quoted_items=quoted_items,
            total_amount=total_amount,
            notes=notes
        )
        
        # Notify buyer
        buyer = get_buyer_by_id(negotiation["buyer_id"])
        if buyer:
            await notify_buyer_quote_ready(buyer, updated, total_amount)
        
        logger.info(f"Vendor {vendor_id} provided quote for {negotiation_id}: ₦{total_amount}")
        return updated
        
    except Exception as e:
        logger.error(f"Quote provision failed: {str(e)}", exc_info=True)
        raise


async def buyer_counter_offer(
    negotiation_id: str,
    buyer_id: str,
    requested_discount: Optional[float] = None,
    counter_total: Optional[float] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Buyer submits counter-offer or discount request.
    
    Args:
        negotiation_id: Negotiation identifier
        buyer_id: Buyer making counter
        requested_discount: Discount percentage (e.g., 10.0 for 10%)
        counter_total: Counter-offer total amount
        notes: Buyer's reasoning
    
    Returns:
        Updated negotiation record
    """
    try:
        # Get negotiation
        negotiation = db_get_negotiation(negotiation_id)
        if not negotiation:
            raise ValueError(f"Negotiation not found: {negotiation_id}")
        
        # Verify buyer
        if negotiation.get("buyer_id") != buyer_id:
            raise ValueError("Not authorized for this negotiation")
        
        # Verify status
        if negotiation.get("status") != "quoted":
            raise ValueError(f"Cannot counter negotiation with status: {negotiation.get('status')}")
        
        # Convert to Decimal
        discount_decimal = Decimal(str(requested_discount)) if requested_discount else None
        counter_decimal = Decimal(str(counter_total)) if counter_total else None
        
        # Update negotiation
        updated = db_add_buyer_counter(
            negotiation_id=negotiation_id,
            buyer_id=buyer_id,
            requested_discount=discount_decimal,
            counter_total=counter_decimal,
            notes=notes
        )
        
        # Notify vendor
        vendor = get_user(negotiation["vendor_id"])
        if vendor:
            await notify_vendor_counter_offer(vendor, updated)
        
        logger.info(f"Buyer {buyer_id} submitted counter-offer for {negotiation_id}")
        return updated
        
    except Exception as e:
        logger.error(f"Counter-offer failed: {str(e)}", exc_info=True)
        raise


async def accept_negotiation(
    negotiation_id: str,
    user_id: str,
    final_amount: Optional[float] = None
) -> Dict[str, Any]:
    """
    Accept the negotiation (by buyer or vendor).
    
    Args:
        negotiation_id: Negotiation identifier
        user_id: User accepting (buyer or vendor)
        final_amount: Final agreed amount
    
    Returns:
        Updated negotiation record
    """
    try:
        # Get negotiation
        negotiation = db_get_negotiation(negotiation_id)
        if not negotiation:
            raise ValueError(f"Negotiation not found: {negotiation_id}")
        
        # Verify authorization
        if user_id not in [negotiation.get("buyer_id"), negotiation.get("vendor_id")]:
            raise ValueError("Not authorized for this negotiation")
        
        # Determine final amount
        if final_amount:
            amount_decimal = Decimal(str(final_amount))
        elif "counter_total" in negotiation:
            amount_decimal = negotiation["counter_total"]
        elif "total_quoted" in negotiation:
            amount_decimal = negotiation["total_quoted"]
        else:
            raise ValueError("No amount specified for acceptance")
        
        # Update status
        updated = db_update_negotiation_status(
            negotiation_id=negotiation_id,
            status="accepted",
            final_amount=amount_decimal
        )
        
        # Notify both parties
        buyer = get_buyer_by_id(negotiation["buyer_id"])
        vendor = get_user(negotiation["vendor_id"])
        
        if buyer:
            await notify_buyer_negotiation_accepted(buyer, updated, amount_decimal)
        if vendor:
            await notify_vendor_negotiation_accepted(vendor, updated, amount_decimal)
        
        logger.info(f"Negotiation {negotiation_id} accepted at ₦{amount_decimal}")
        return updated
        
    except Exception as e:
        logger.error(f"Accept negotiation failed: {str(e)}", exc_info=True)
        raise


async def reject_negotiation(
    negotiation_id: str,
    user_id: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reject the negotiation.
    
    Args:
        negotiation_id: Negotiation identifier
        user_id: User rejecting (buyer or vendor)
        reason: Optional rejection reason
    
    Returns:
        Updated negotiation record
    """
    try:
        # Get negotiation
        negotiation = db_get_negotiation(negotiation_id)
        if not negotiation:
            raise ValueError(f"Negotiation not found: {negotiation_id}")
        
        # Verify authorization
        if user_id not in [negotiation.get("buyer_id"), negotiation.get("vendor_id")]:
            raise ValueError("Not authorized for this negotiation")
        
        # Update status
        updated = db_update_negotiation_status(
            negotiation_id=negotiation_id,
            status="rejected"
        )
        
        logger.info(f"Negotiation {negotiation_id} rejected by {user_id}")
        return updated
        
    except Exception as e:
        logger.error(f"Reject negotiation failed: {str(e)}", exc_info=True)
        raise


# Notification helpers (similar to order notifications)
async def notify_vendor_new_quote_request(vendor, buyer, negotiation):
    """Notify vendor of new quote request."""
    try:
        message = f"📋 *New Quote Request*\n\n"
        message += f"From: Buyer {buyer.get('phone', 'Unknown')[-4:]}\n"
        message += f"Items: {len(negotiation['items'])}\n\n"
        
        for idx, item in enumerate(negotiation['items'], 1):
            message += f"{idx}. {item['name']} × {item['quantity']}\n"
        
        if negotiation.get('notes'):
            message += f"\nNotes: {negotiation['notes']}\n"
        
        message += f"\nPlease provide pricing via the vendor dashboard."
        
        # Send via vendor's preferred channel (SMS for now)
        logger.info(f"Quote request notification prepared for vendor {vendor.get('user_id')}")
        
    except Exception as e:
        logger.error(f"Failed to notify vendor: {str(e)}")


async def notify_buyer_quote_ready(buyer, negotiation, total):
    """Notify buyer that quote is ready."""
    try:
        message = f"💰 *Quote Ready!*\n\n"
        message += f"Total: ₦{total:,}\n\n"
        message += f"View details and accept/counter-offer in your app."
        
        # Send via buyer's platform
        logger.info(f"Quote ready notification prepared for buyer {buyer.get('user_id')}")
        
    except Exception as e:
        logger.error(f"Failed to notify buyer: {str(e)}")


async def notify_vendor_counter_offer(vendor, negotiation):
    """Notify vendor of buyer counter-offer."""
    logger.info(f"Counter-offer notification prepared for vendor")


async def notify_buyer_negotiation_accepted(buyer, negotiation, amount):
    """Notify buyer negotiation was accepted."""
    logger.info(f"Acceptance notification prepared for buyer")


async def notify_vendor_negotiation_accepted(vendor, negotiation, amount):
    """Notify vendor negotiation was accepted."""
    logger.info(f"Acceptance notification prepared for vendor")
