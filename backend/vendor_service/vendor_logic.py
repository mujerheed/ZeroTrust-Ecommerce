"""
Complete business logic for vendor operations.
Handles order management, receipt verification, and vendor dashboard features.
Includes high-value escalation workflow (₦1M+) requiring CEO approval.
"""

from typing import List, Dict, Optional
from .database import (
    get_vendor, get_vendor_assigned_orders, get_order, get_receipt,
    update_order_status, get_vendor_stats, log_vendor_action
)
from common.config import settings
from common.escalation_db import create_escalation
from common.sns_client import send_escalation_alert, send_buyer_notification
from common.logger import logger

def get_vendor_dashboard_data(vendor_id: str) -> Dict:
    """Get complete vendor dashboard data."""
    # Verify vendor exists and is active
    vendor = get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found or inactive")
    
    # Get dashboard statistics
    stats = get_vendor_stats(vendor_id)
    
    # Get pending orders that need attention
    pending_orders = get_vendor_assigned_orders(vendor_id, "pending_receipt")
    
    # Enhance orders with receipt info
    for order in pending_orders:
        order["receipt"] = get_receipt(order["order_id"])
    
    log_vendor_action(vendor_id, "DASHBOARD_ACCESSED")
    
    return {
        "vendor_info": {
            "vendor_id": vendor["user_id"],
            "name": vendor["name"],
            "email": vendor.get("email", ""),
            "phone": vendor.get("phone", "")
        },
        "statistics": stats,
        "pending_orders": pending_orders[:10]  # Limit to 10 most recent
    }

def get_vendor_orders(vendor_id: str, status: str = None, limit: int = 50) -> List[Dict]:
    """Get vendor's assigned orders with optional filtering."""
    vendor = get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    
    orders = get_vendor_assigned_orders(vendor_id, status)
    
    # Limit results and add receipt info
    limited_orders = orders[:limit]
    for order in limited_orders:
        order["receipt"] = get_receipt(order["order_id"])
    
    log_vendor_action(vendor_id, "ORDERS_VIEWED", details={"status_filter": status, "count": len(limited_orders)})
    
    return limited_orders

def check_escalation_required(order: Dict, manual_flag: bool = False) -> tuple[bool, str]:
    """
    Check if order requires CEO escalation.
    
    Args:
        order: Order dictionary with amount and other details
        manual_flag: True if vendor manually flagged the receipt
    
    Returns:
        tuple: (requires_escalation: bool, reason: str)
    """
    amount = float(order.get("amount", 0))
    
    # Check high-value threshold (₦1,000,000+)
    if amount >= settings.HIGH_VALUE_THRESHOLD:
        return (True, "HIGH_VALUE")
    
    # Check manual vendor flag
    if manual_flag:
        return (True, "VENDOR_FLAGGED")
    
    # Future: Textract low confidence score
    # textract_confidence = order.get("textract_confidence", 100)
    # if textract_confidence < 70:
    #     return (True, "TEXTRACT_LOW_CONFIDENCE")
    
    return (False, "")

def create_order_escalation(order: Dict, vendor_id: str, reason: str, notes: str = None) -> str:
    """
    Create escalation record and notify CEO.
    
    Args:
        order: Order dictionary
        vendor_id: Vendor who is escalating
        reason: Escalation reason
        notes: Optional vendor notes
    
    Returns:
        str: escalation_id
    
    Raises:
        Exception: If escalation creation fails
    """
    order_id = order["order_id"]
    ceo_id = order.get("ceo_id")
    
    if not ceo_id:
        raise ValueError("Order missing ceo_id - cannot escalate")
    
    # Create escalation record
    escalation_id = create_escalation(
        order_id=order_id,
        ceo_id=ceo_id,
        vendor_id=vendor_id,
        buyer_id=order.get("buyer_id", "unknown"),
        amount=float(order.get("amount", 0)),
        reason=reason,
        flagged_by=vendor_id if reason == "VENDOR_FLAGGED" else None,
        notes=notes
    )
    
    logger.info(
        f"Escalation created: {escalation_id} for order {order_id}, "
        f"reason={reason}, amount=₦{order.get('amount', 0):,.2f}"
    )
    
    # Send CEO alert (SMS + Email via SNS)
    vendor = get_vendor(vendor_id)
    vendor_name = vendor.get("name", "Unknown Vendor") if vendor else "Unknown Vendor"
    
    # Mask buyer phone for CEO notification
    buyer_phone = order.get("buyer_phone", "")
    masked_phone = buyer_phone[-4:] if len(buyer_phone) >= 4 else "****"
    
    send_escalation_alert(
        ceo_id=ceo_id,
        escalation_id=escalation_id,
        order_id=order_id,
        amount=float(order.get("amount", 0)),
        reason=reason,
        vendor_name=vendor_name,
        buyer_masked_phone=masked_phone
    )
    
    # Notify buyer: "Order under review"
    if buyer_phone:
        send_buyer_notification(
            buyer_phone=buyer_phone,
            order_id=order_id,
            status="Under Review",
            additional_message=(
                "Your order has been flagged for security verification. "
                "Our team will review it within 24 hours. Thank you for your patience."
            )
        )
    
    return escalation_id

def get_order_details(vendor_id: str, order_id: str) -> Dict:
    """Get detailed information about a specific order."""
    vendor = get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    
    order = get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    
    # Verify this vendor is assigned to this order
    if order.get("vendor_id") != vendor_id:
        raise ValueError("Access denied: Order not assigned to this vendor")
    
    # Get receipt details
    receipt = get_receipt(order_id)
    
    # Get buyer information (limited to what vendor should see)
    buyer_info = {
        "buyer_id": order.get("buyer_id"),
        "buyer_name": order.get("buyer_name"),
        "delivery_address": order.get("delivery_address"),
        "buyer_phone": order.get("buyer_phone")  # Vendor needs this for delivery
    }
    
    log_vendor_action(vendor_id, "ORDER_DETAILS_VIEWED", order_id=order_id)
    
    return {
        "order": order,
        "buyer": buyer_info,
        "receipt": receipt
    }

def verify_receipt(vendor_id: str, order_id: str, verification_status: str, notes: str = None) -> Dict:
    """
    Vendor verifies or flags a receipt.
    
    Zero Trust Escalation Workflow:
    1. Check if amount >= ₦1M or vendor manually flags
    2. If escalation required: auto-pause order, notify CEO, notify buyer
    3. If no escalation: proceed with normal verification
    
    Args:
        vendor_id: Vendor performing verification
        order_id: Order being verified
        verification_status: 'verified' or 'flagged'
        notes: Optional vendor notes
    
    Returns:
        Dict with order_id, new_status, escalation details if applicable
    """
    if verification_status not in ['verified', 'flagged']:
        raise ValueError("Invalid verification status. Use 'verified' or 'flagged'")
    
    vendor = get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    
    order = get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    
    # Verify vendor assignment
    if order.get("vendor_id") != vendor_id:
        raise ValueError("Access denied: Order not assigned to this vendor")
    
    # Check if order is in correct state for verification
    if order.get("order_status") != "pending_receipt":
        raise ValueError(f"Order status '{order.get('order_status')}' cannot be verified")
    
    # ===== ESCALATION DETECTION =====
    manual_flag = (verification_status == "flagged")
    requires_escalation, escalation_reason = check_escalation_required(order, manual_flag)
    
    if requires_escalation:
        # Auto-pause order for CEO review
        update_order_status(order_id, "escalated", vendor_id, notes)
        
        # Create escalation record and notify CEO + buyer
        escalation_id = create_order_escalation(
            order=order,
            vendor_id=vendor_id,
            reason=escalation_reason,
            notes=notes
        )
        
        # Log escalation action
        log_vendor_action(vendor_id, "ORDER_ESCALATED", order_id=order_id, details={
            "escalation_id": escalation_id,
            "reason": escalation_reason,
            "amount": order.get("amount"),
            "notes": notes or "No notes provided"
        })
        
        return {
            "order_id": order_id,
            "new_status": "escalated",
            "escalation_id": escalation_id,
            "escalation_reason": escalation_reason,
            "message": (
                f"Order escalated to CEO for approval. "
                f"Reason: {escalation_reason}. "
                f"Amount: ₦{order.get('amount', 0):,.2f}"
            ),
            "requires_ceo_approval": True,
            "buyer_notified": True
        }
    
    # ===== NORMAL VERIFICATION (No Escalation) =====
    new_status = verification_status
    update_order_status(order_id, new_status, vendor_id, notes)
    
    # Log the verification action
    action = "RECEIPT_VERIFIED" if verification_status == "verified" else "RECEIPT_FLAGGED"
    log_vendor_action(vendor_id, action, order_id=order_id, details={
        "verification_status": verification_status,
        "notes": notes or "No notes provided"
    })
    
    return {
        "order_id": order_id,
        "new_status": new_status,
        "message": f"Receipt {verification_status} successfully",
        "requires_ceo_approval": False
    }

def get_receipt_details(vendor_id: str, order_id: str) -> Dict:
    """Get detailed receipt information for verification."""
    vendor = get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    
    order = get_order(order_id)
    if not order or order.get("vendor_id") != vendor_id:
        raise ValueError("Order not found or access denied")
    
    receipt = get_receipt(order_id)
    if not receipt:
        raise ValueError("Receipt not found for this order")
    
    log_vendor_action(vendor_id, "RECEIPT_VIEWED", order_id=order_id)
    
    return {
        "receipt": receipt,
        "order_amount": order.get("amount"),
        "buyer_name": order.get("buyer_name"),
        "verification_guidelines": {
            "check_payer_name": "Verify payer name matches buyer",
            "check_amount": f"Verify amount is ₦{order.get('amount', 0):,.2f}",
            "check_timestamp": "Verify payment is recent",
            "check_bank": "Verify bank details are clear"
        }
    }

def search_vendor_orders(vendor_id: str, search_term: str, search_field: str = "buyer_name") -> List[Dict]:
    """Search through vendor's assigned orders."""
    vendor = get_vendor(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    
    all_orders = get_vendor_assigned_orders(vendor_id)
    
    # Filter orders based on search term and field
    if search_field == "buyer_name":
        filtered_orders = [
            order for order in all_orders 
            if search_term.lower() in order.get("buyer_name", "").lower()
        ]
    elif search_field == "order_id":
        filtered_orders = [
            order for order in all_orders 
            if search_term.lower() in order.get("order_id", "").lower()
        ]
    elif search_field == "buyer_phone":
        filtered_orders = [
            order for order in all_orders 
            if search_term in order.get("buyer_phone", "")
        ]
    else:
        raise ValueError("Invalid search field")
    
    log_vendor_action(vendor_id, "ORDERS_SEARCHED", details={
        "search_term": search_term, 
        "search_field": search_field,
        "results_count": len(filtered_orders)
    })
    
    return filtered_orders[:20]  # Limit to 20 results
