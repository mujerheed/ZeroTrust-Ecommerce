"""
Business logic for CEO operations.
"""

import time
import secrets
import random
import string
from typing import Dict, Any, List, Optional
from .database import (
    get_all_vendors, get_vendor_by_id, create_vendor, delete_vendor,
    get_flagged_transactions, update_order_status, get_audit_logs,
    get_order_by_id, get_user_by_id
)
from auth_service.database import save_otp, get_otp, delete_otp
from common.escalation_db import (
    get_pending_escalations, get_escalation, update_escalation_status
)
from common.sns_client import send_buyer_notification, send_escalation_resolved_notification
from common.logger import logger

# OTP settings
OTP_TTL      = 300
OTP_LENGTH   = 6

def generate_ceo_otp(user_id: str) -> str:
    """Generate and store a 6-character OTP for a CEO."""
    chars = string.digits + string.punctuation
    otp   = ''.join(random.choices(chars, k=OTP_LENGTH))
    save_otp(user_id, otp, "CEO", OTP_TTL)
    return otp

def initiate_ceo_signup(name: str, phone: str, email: str) -> str:
    """Create pending CEO entry and send signup OTP."""
    ceo_id = f"ceo_{secrets.token_hex(4)}"
    otp    = generate_ceo_otp(ceo_id)
    # TODO: send OTP via SMS/Email
    print(f"[CEO Signup] OTP for {ceo_id}: {otp}")
    return ceo_id

def verify_ceo_signup(user_id: str, submitted_otp: str, profile: Dict[str, Any]) -> str:
    """Verify OTP, then create CEO user record."""
    record = get_otp(user_id)
    if not record or record["role"] != "CEO" or record["otp_code"] != submitted_otp:
        raise ValueError("Invalid or expired OTP")
    delete_otp(user_id)
    # Create CEO in USERS_TABLE
    vendor = {
        "user_id": user_id,
        "name": profile["name"],
        "phone": profile["phone"],
        "email": profile["email"],
        "role": "CEO",
        "created_by": user_id,
        "created_at": int(time.time()),
        "settings": profile.get("settings", {})
    }
    create_vendor(vendor)
    return user_id

def login_ceo(contact: str) -> str:
    """Send login OTP to CEO via phone/email lookup."""
    # Lookup CEO user_id by contact
    # (scan or query by email/phone; omitted for brevity)
    ceo_user = None  # implement lookup
    if not ceo_user:
        raise ValueError("CEO not found")
    user_id = ceo_user["user_id"]
    otp     = generate_ceo_otp(user_id)
    # TODO: send OTP
    print(f"[CEO Login] OTP for {user_id}: {otp}")
    return user_id

def list_vendors() -> List[Dict[str, Any]]:
    """Return all vendor accounts."""
    return get_all_vendors()

def add_vendor(name: str, phone: str, email: str, created_by: str) -> str:
    """Create a new vendor; generate user_id and store."""
    vendor_id = f"vendor_{secrets.token_hex(4)}"
    vendor    = {
        "user_id": vendor_id,
        "name": name,
        "phone": phone,
        "email": email,
        "role": "Vendor",
        "created_by": created_by,
        "created_at": int(time.time())
    }
    return create_vendor(vendor)

def remove_vendor(vendor_id: str):
    """Delete a vendor account by user_id."""
    if not get_vendor_by_id(vendor_id):
        raise ValueError("Vendor not found")
    delete_vendor(vendor_id)

def view_flagged_orders() -> List[Dict[str, Any]]:
    """Retrieve all flagged or high-value transactions."""
    return get_flagged_transactions()

def approve_transaction(order_id: str, ceo_id: str):
    """CEO approves a flagged or high-value order."""
    update_order_status(order_id, "verified", ceo_id)

def decline_transaction(order_id: str, ceo_id: str):
    """CEO declines a flagged or high-value order."""
    update_order_status(order_id, "declined", ceo_id)

def fetch_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch recent audit logs entries."""
    return get_audit_logs(limit)


def get_ceo_pending_escalations(ceo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve all pending escalations for CEO approval.
    
    Returns enriched escalation data with order and user details.
    """
    escalations = get_pending_escalations(ceo_id, limit)
    
    enriched_escalations = []
    for esc in escalations:
        try:
            # Get order details
            order = get_order_by_id(esc['order_id'])
            if not order:
                logger.warning(f"Order not found for escalation {esc['escalation_id']}")
                continue
            
            # Get buyer details (masked)
            buyer = get_user_by_id(esc['buyer_id'])
            buyer_name = buyer.get('name', 'Unknown') if buyer else 'Unknown'
            buyer_phone_masked = esc['buyer_id'][-4:] if len(esc['buyer_id']) >= 4 else "****"
            
            # Get vendor details
            vendor = get_user_by_id(esc['vendor_id'])
            vendor_name = vendor.get('name', 'Unknown Vendor') if vendor else 'Unknown Vendor'
            
            # Build enriched escalation object
            enriched_escalations.append({
                'escalation_id': esc['escalation_id'],
                'order_id': esc['order_id'],
                'vendor_id': esc['vendor_id'],
                'vendor_name': vendor_name,
                'buyer_id': esc['buyer_id'],
                'buyer_name': buyer_name,
                'buyer_phone_masked': f"***{buyer_phone_masked}",
                'amount': esc['amount'],
                'reason': esc['reason'],
                'status': esc['status'],
                'notes': esc.get('notes', ''),
                'flagged_by': esc.get('flagged_by'),
                'created_at': esc['created_at'],
                'expires_at': esc['expires_at'],
                'order_details': {
                    'product': order.get('product_name', 'N/A'),
                    'quantity': order.get('quantity', 1),
                    'delivery_address': order.get('delivery_address', 'N/A'),
                    'receipt_url': order.get('receipt_url', ''),
                    'textract_results': order.get('textract_results', {})
                }
            })
        except Exception as e:
            logger.error(f"Error enriching escalation {esc.get('escalation_id')}: {str(e)}")
            continue
    
    return enriched_escalations


def get_escalation_details(ceo_id: str, escalation_id: str) -> Dict[str, Any]:
    """
    Get full details of a specific escalation for CEO review.
    
    Includes order context, receipt preview, Textract results, and vendor notes.
    """
    # Verify escalation exists and belongs to this CEO
    escalation = get_escalation(escalation_id)
    if not escalation:
        raise ValueError(f"Escalation {escalation_id} not found")
    
    if escalation['ceo_id'] != ceo_id:
        raise ValueError("Unauthorized: escalation belongs to different CEO")
    
    # Get order details
    order = get_order_by_id(escalation['order_id'])
    if not order:
        raise ValueError(f"Order {escalation['order_id']} not found")
    
    # Get buyer and vendor details
    buyer = get_user_by_id(escalation['buyer_id'])
    vendor = get_user_by_id(escalation['vendor_id'])
    
    # Mask sensitive buyer information
    buyer_phone_masked = escalation['buyer_id'][-4:] if len(escalation['buyer_id']) >= 4 else "****"
    
    return {
        'escalation': {
            'escalation_id': escalation['escalation_id'],
            'status': escalation['status'],
            'reason': escalation['reason'],
            'amount': escalation['amount'],
            'notes': escalation.get('notes', ''),
            'flagged_by': escalation.get('flagged_by'),
            'created_at': escalation['created_at'],
            'expires_at': escalation['expires_at']
        },
        'order': {
            'order_id': order['order_id'],
            'product_name': order.get('product_name', 'N/A'),
            'quantity': order.get('quantity', 1),
            'amount': order.get('amount', 0),
            'status': order.get('order_status', 'unknown'),
            'delivery_address': order.get('delivery_address', 'N/A'),
            'receipt_url': order.get('receipt_url', ''),
            'receipt_metadata': order.get('receipt_metadata', {}),
            'textract_results': order.get('textract_results', {}),
            'created_at': order.get('created_at', 0)
        },
        'buyer': {
            'buyer_id': escalation['buyer_id'],
            'name': buyer.get('name', 'Unknown') if buyer else 'Unknown',
            'phone_masked': f"***{buyer_phone_masked}"
        },
        'vendor': {
            'vendor_id': escalation['vendor_id'],
            'name': vendor.get('name', 'Unknown Vendor') if vendor else 'Unknown Vendor',
            'email': vendor.get('email', '') if vendor else ''
        }
    }


def approve_escalation_with_otp(
    ceo_id: str,
    escalation_id: str,
    otp: str,
    decision_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Approve an escalation after OTP verification.
    
    Zero Trust: Requires fresh OTP for approval action.
    """
    # Verify OTP
    otp_record = get_otp(ceo_id)
    if not otp_record or otp_record.get('otp_code') != otp:
        raise ValueError("Invalid or expired OTP")
    
    # Delete OTP (single-use)
    delete_otp(ceo_id)
    
    # Get escalation details
    escalation = get_escalation(escalation_id)
    if not escalation:
        raise ValueError(f"Escalation {escalation_id} not found")
    
    if escalation['ceo_id'] != ceo_id:
        raise ValueError("Unauthorized: escalation belongs to different CEO")
    
    if escalation['status'] != 'PENDING':
        raise ValueError(f"Cannot approve escalation with status: {escalation['status']}")
    
    # Update escalation status
    success = update_escalation_status(
        escalation_id=escalation_id,
        status='APPROVED',
        approved_by=ceo_id,
        decision_notes=decision_notes
    )
    
    if not success:
        raise ValueError("Failed to update escalation status")
    
    # Update order status to proceed with fulfillment
    update_order_status(
        order_id=escalation['order_id'],
        new_status='approved',
        ceo_id=ceo_id
    )
    
    # Send notifications
    order = get_order_by_id(escalation['order_id'])
    if order:
        # Notify buyer
        buyer = get_user_by_id(escalation['buyer_id'])
        if buyer and buyer.get('phone'):
            send_buyer_notification(
                buyer_phone=buyer['phone'],
                order_id=escalation['order_id'],
                status='Approved',
                additional_message=f"Your order of ₦{escalation['amount']:,.2f} has been approved and will be processed for delivery."
            )
    
    # Send resolution notification to CEO
    send_escalation_resolved_notification(
        ceo_id=ceo_id,
        escalation_id=escalation_id,
        order_id=escalation['order_id'],
        decision='APPROVED',
        amount=escalation['amount']
    )
    
    logger.info(
        f"Escalation {escalation_id} APPROVED by CEO {ceo_id}",
        extra={
            'escalation_id': escalation_id,
            'order_id': escalation['order_id'],
            'ceo_id': ceo_id,
            'amount': escalation['amount'],
            'decision': 'APPROVED'
        }
    )
    
    return {
        'escalation_id': escalation_id,
        'order_id': escalation['order_id'],
        'decision': 'APPROVED',
        'amount': escalation['amount'],
        'buyer_notified': True,
        'vendor_notified': True
    }


def reject_escalation_with_otp(
    ceo_id: str,
    escalation_id: str,
    otp: str,
    decision_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reject an escalation after OTP verification.
    
    Zero Trust: Requires fresh OTP for rejection action.
    """
    # Verify OTP
    otp_record = get_otp(ceo_id)
    if not otp_record or otp_record.get('otp_code') != otp:
        raise ValueError("Invalid or expired OTP")
    
    # Delete OTP (single-use)
    delete_otp(ceo_id)
    
    # Get escalation details
    escalation = get_escalation(escalation_id)
    if not escalation:
        raise ValueError(f"Escalation {escalation_id} not found")
    
    if escalation['ceo_id'] != ceo_id:
        raise ValueError("Unauthorized: escalation belongs to different CEO")
    
    if escalation['status'] != 'PENDING':
        raise ValueError(f"Cannot reject escalation with status: {escalation['status']}")
    
    # Update escalation status
    success = update_escalation_status(
        escalation_id=escalation_id,
        status='REJECTED',
        approved_by=ceo_id,
        decision_notes=decision_notes
    )
    
    if not success:
        raise ValueError("Failed to update escalation status")
    
    # Update order status to canceled
    update_order_status(
        order_id=escalation['order_id'],
        new_status='rejected',
        ceo_id=ceo_id
    )
    
    # Send notifications
    order = get_order_by_id(escalation['order_id'])
    if order:
        # Notify buyer
        buyer = get_user_by_id(escalation['buyer_id'])
        if buyer and buyer.get('phone'):
            reason_text = decision_notes or "Transaction verification failed"
            send_buyer_notification(
                buyer_phone=buyer['phone'],
                order_id=escalation['order_id'],
                status='Rejected',
                additional_message=f"Your order of ₦{escalation['amount']:,.2f} has been rejected. Reason: {reason_text}. Please contact support for assistance."
            )
    
    # Send resolution notification to CEO
    send_escalation_resolved_notification(
        ceo_id=ceo_id,
        escalation_id=escalation_id,
        order_id=escalation['order_id'],
        decision='REJECTED',
        amount=escalation['amount']
    )
    
    logger.info(
        f"Escalation {escalation_id} REJECTED by CEO {ceo_id}",
        extra={
            'escalation_id': escalation_id,
            'order_id': escalation['order_id'],
            'ceo_id': ceo_id,
            'amount': escalation['amount'],
            'decision': 'REJECTED',
            'reason': decision_notes
        }
    )
    
    return {
        'escalation_id': escalation_id,
        'order_id': escalation['order_id'],
        'decision': 'REJECTED',
        'amount': escalation['amount'],
        'buyer_notified': True,
        'vendor_notified': True
    }

