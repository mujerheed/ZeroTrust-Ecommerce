"""
Auto-approval logic for vendor receipts based on preferences.

This module checks vendor preferences and automatically approves
low-value receipts below the configured threshold.
"""

import time
from typing import Dict, Tuple
from common.logger import logger
from .preferences import get_vendor_preferences
from .database import get_order, update_order_status, log_vendor_action


def check_auto_approve_eligible(vendor_id: str, order: Dict) -> Tuple[bool, str]:
    """
    Check if an order is eligible for auto-approval based on vendor preferences.
    
    Args:
        vendor_id: Vendor identifier
        order: Order dictionary
    
    Returns:
        Tuple of (is_eligible: bool, reason: str)
    """
    # Get vendor preferences
    preferences = get_vendor_preferences(vendor_id)
    auto_approve_threshold = preferences.get("auto_approve_threshold", 0)
    
    # If threshold is 0, auto-approve is disabled
    if auto_approve_threshold == 0:
        return False, "Auto-approve disabled (threshold = 0)"
    
    # Get order amount (in kobo)
    order_amount = order.get("amount", 0)
    
    # Check if amount is below threshold
    if order_amount < auto_approve_threshold:
        return True, f"Amount ₦{order_amount/100:,.2f} below threshold ₦{auto_approve_threshold/100:,.2f}"
    else:
        return False, f"Amount ₦{order_amount/100:,.2f} exceeds threshold ₦{auto_approve_threshold/100:,.2f}"


async def process_receipt_auto_approve(vendor_id: str, order_id: str) -> Dict:
    """
    Process receipt upload and check if auto-approval should be applied.
    
    This function is called after a buyer uploads a receipt.
    If the order amount is below the vendor's auto-approve threshold,
    the receipt is automatically approved without manual review.
    
    Args:
        vendor_id: Vendor identifier
        order_id: Order identifier
    
    Returns:
        Dict with auto_approve_applied: bool and status: str
    """
    try:
        # Get order details
        order = get_order(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found for auto-approve check")
            return {"auto_approve_applied": False, "status": "order_not_found"}
        
        # Check if order belongs to this vendor
        if order.get("vendor_id") != vendor_id:
            logger.warning(f"Order {order_id} does not belong to vendor {vendor_id}")
            return {"auto_approve_applied": False, "status": "vendor_mismatch"}
        
        # Check current order status
        current_status = order.get("order_status", "unknown")
        if current_status not in ["pending_receipt", "receipt_uploaded"]:
            logger.info(f"Order {order_id} status {current_status} - skipping auto-approve")
            return {"auto_approve_applied": False, "status": f"invalid_status_{current_status}"}
        
        # Check if eligible for auto-approval
        is_eligible, reason = check_auto_approve_eligible(vendor_id, order)
        
        if not is_eligible:
            logger.info(f"Order {order_id} not eligible for auto-approve: {reason}")
            return {
                "auto_approve_applied": False,
                "status": "not_eligible",
                "reason": reason
            }
        
        # Auto-approve the receipt
        update_order_status(
            order_id=order_id,
            new_status="verified",
            updated_by=f"{vendor_id}_auto",  # Mark as auto-approved
            notes=f"Auto-approved: {reason}"
        )
        
        # Log the auto-approval action
        log_vendor_action(
            vendor_id=vendor_id,
            action="RECEIPT_AUTO_APPROVED",
            order_id=order_id,
            details={
                "threshold": get_vendor_preferences(vendor_id).get("auto_approve_threshold"),
                "order_amount": order.get("amount"),
                "reason": reason,
                "timestamp": int(time.time())
            }
        )
        
        logger.info(
            f"Receipt auto-approved for order {order_id}",
            extra={
                "vendor_id": vendor_id,
                "order_id": order_id,
                "amount": order.get("amount"),
                "reason": reason
            }
        )
        
        return {
            "auto_approve_applied": True,
            "status": "verified",
            "reason": reason,
            "order_id": order_id
        }
    
    except Exception as e:
        logger.error(
            f"Auto-approve failed for order {order_id}: {str(e)}",
            extra={"vendor_id": vendor_id, "error": str(e)}
        )
        return {
            "auto_approve_applied": False,
            "status": "error",
            "error": str(e)
        }
