"""
Complete business logic for vendor operations.
Handles order management, receipt verification, and vendor dashboard features.
"""

from typing import List, Dict, Optional
from database import (
    get_vendor, get_vendor_assigned_orders, get_order, get_receipt,
    update_order_status, get_vendor_stats, log_vendor_action
)

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
    verification_status: 'verified' or 'flagged'
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
    
    # Update order status
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
        "requires_ceo_approval": verification_status == "flagged"
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
