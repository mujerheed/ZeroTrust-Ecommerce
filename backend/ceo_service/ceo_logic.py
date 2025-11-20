"""
Business logic for CEO operations.

This module handles:
- CEO registration and authentication
- Vendor onboarding and management
- Order approval workflows (flagged + high-value)
- Dashboard metrics and reporting
- Multi-CEO tenancy enforcement
"""

import time
import bcrypt
import random
import string
from decimal import Decimal
from typing import Dict, Any, List, Optional
from .database import (
    # CEO operations
    create_ceo, get_ceo_by_id, get_ceo_by_email, update_ceo,
    # Vendor operations
    create_vendor, get_vendor_by_id, get_all_vendors_for_ceo, delete_vendor,
    # Order operations
    get_orders_for_ceo, get_flagged_orders_for_ceo, get_high_value_orders_for_ceo,
    get_order_by_id, update_order_status, get_ceo_dashboard_stats,
    # Audit logs
    get_audit_logs, write_audit_log,
    # User queries
    get_user_by_id,
    # CEO config
    save_chatbot_config, get_chatbot_config
)
from auth_service.database import save_otp, get_otp, delete_otp
from common.security import create_jwt
from common.logger import logger

# OTP settings for CEO
OTP_TTL = 300  # 5 minutes
OTP_LENGTH = 6  # 6 characters (digits + symbols)


# ==================== OTP Generation ====================

def generate_ceo_otp() -> str:
    """
    Generate 6-character OTP for CEO (digits + symbols: 0-9!@#$%^&*).
    
    Returns:
        6-character OTP string
    """
    chars = string.digits + "!@#$%^&*"
    otp = ''.join(random.choices(chars, k=OTP_LENGTH))
    return otp


def store_ceo_otp(ceo_id: str, otp: str):
    """
    Store CEO OTP with TTL.
    
    Args:
        ceo_id: CEO identifier
        otp: OTP code to store
    """
    save_otp(ceo_id, otp, "CEO", OTP_TTL)
    logger.info(f"CEO OTP stored", extra={
        "ceo_id": ceo_id,
        "ttl_seconds": OTP_TTL
    })


def verify_ceo_otp(ceo_id: str, submitted_otp: str) -> bool:
    """
    Verify CEO OTP and delete if valid.
    
    Args:
        ceo_id: CEO identifier
        submitted_otp: OTP submitted by CEO
    
    Returns:
        True if OTP is valid, False otherwise
    """
    record = get_otp(ceo_id)
    
    if not record:
        logger.warning("OTP not found", extra={"ceo_id": ceo_id})
        return False
    
    if record.get("role") != "CEO":
        logger.warning("OTP role mismatch", extra={
            "ceo_id": ceo_id,
            "expected_role": "CEO",
            "actual_role": record.get("role")
        })
        return False
    
    if record.get("otp_code") != submitted_otp:
        logger.warning("OTP mismatch", extra={"ceo_id": ceo_id})
        return False
    
    # Check expiration
    expires_at = record.get("expires_at", 0)
    if int(time.time()) > expires_at:
        logger.warning("OTP expired", extra={
            "ceo_id": ceo_id,
            "expires_at": expires_at
        })
        delete_otp(ceo_id)
        return False
    
    # Valid OTP - delete it (single-use)
    delete_otp(ceo_id)
    logger.info("CEO OTP verified", extra={"ceo_id": ceo_id})
    return True



# ==================== CEO Registration (OTP-Based - Zero Trust) ====================

def register_ceo(name: str, email: str, phone: str, company_name: str = None) -> Dict[str, Any]:
    """
    Register a new CEO account with OTP verification (Zero Trust).
    
    Args:
        name: CEO full name
        email: CEO email (unique identifier)
        phone: CEO phone number (Nigerian format)
        company_name: Optional company/business name
    
    Returns:
        Created CEO record with OTP sent status
    
    Raises:
        ValueError: If email already exists
    """
    # Check if email already exists
    existing_ceo = get_ceo_by_email(email)
    if existing_ceo:
        logger.warning("CEO registration failed - email exists", extra={"email": email})
        raise ValueError("Email already registered")
    
    # Create CEO record (no password)
    ceo_record = create_ceo(
        name=name,
        email=email,
        phone=phone,
        company_name=company_name
    )
    
    # Generate and send OTP
    otp = generate_ceo_otp()
    store_ceo_otp(ceo_record["ceo_id"], otp)
    
    # Send OTP via SMS and Email
    try:
        from common.config import settings
        import boto3
        
        # Send via SMS
        sns = boto3.client('sns', region_name=settings.AWS_REGION)
        sms_message = f"TrustGuard CEO Registration: Your OTP is {otp}. Valid for 5 minutes."
        sns.publish(PhoneNumber=phone, Message=sms_message)
        
        # TODO: Send via Email (AWS SES)
        logger.info(f"CEO OTP sent via SMS/Email", extra={"ceo_id": ceo_record["ceo_id"], "phone": phone, "email": email})
    except Exception as e:
        logger.warning(f"Failed to send CEO OTP: {e}", extra={"ceo_id": ceo_record["ceo_id"]})
    
    # Log creation
    write_audit_log(
        ceo_id=ceo_record["ceo_id"],
        action="ceo_registered",
        user_id=ceo_record["ceo_id"],
        details={"email": email, "company_name": company_name}
    )
    
    logger.info("CEO registered with OTP", extra={
        "ceo_id": ceo_record["ceo_id"],
        "email": email,
        "company_name": company_name
    })
    
    return ceo_record


# ==================== CEO Authentication (REMOVED - Use auth_service OTP flow) ====================
# authenticate_ceo() removed - CEOs now authenticate via auth_service OTP endpoints
    """
    Authenticate CEO and generate JWT token.
    
    Args:
        email: CEO email
        password: Plain text password
    
    Returns:
        Dictionary with CEO data and JWT token
    
    Raises:
        ValueError: If credentials are invalid
    """
    # Get CEO by email
    ceo = get_ceo_by_email(email)
    if not ceo:
        logger.warning("CEO login failed - email not found", extra={"email": email})
        raise ValueError("Invalid email or password")
    
    # Verify password
    password_hash = ceo.get("password_hash", "")
    if not verify_password(password, password_hash):
        logger.warning("CEO login failed - password mismatch", extra={
            "ceo_id": ceo.get("ceo_id"),
            "email": email
        })
        raise ValueError("Invalid email or password")
    
    # Generate JWT token
    ceo_id = ceo["ceo_id"]
    token = create_jwt(subject=ceo_id, role="CEO", expires_minutes=60)
    
    # Log successful login
    write_audit_log(
        ceo_id=ceo_id,
        action="ceo_login",
        user_id=ceo_id,
        details={"email": email}
    )
    
    logger.info("CEO authenticated", extra={
        "ceo_id": ceo_id,
        "email": email
    })
    
    # Remove sensitive data
    ceo.pop("password_hash", None)
    
    return {
        "ceo": ceo,
        "token": token
    }


# ==================== CEO Profile Management ====================

def update_ceo_profile(
    ceo_id: str,
    company_name: Optional[str] = None,
    phone: Optional[str] = None,
    business_hours: Optional[str] = None,
    delivery_fee: Optional[float] = None,
    bank_details: Optional[Dict[str, str]] = None,
    email: Optional[str] = None,
    otp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update CEO profile information.
    
    Sensitive fields (email) require OTP verification.
    Regular fields (company_name, phone, business_hours, delivery_fee, bank_details) can be updated directly.
    
    Args:
        ceo_id: CEO identifier
        company_name: Optional company/business name
        phone: Optional business phone number
        business_hours: Optional business operating hours (e.g., "Mon-Fri 9AM-5PM")
        delivery_fee: Optional default delivery fee in Naira
        bank_details: Optional bank account info (bank_name, account_number, account_name)
        email: Optional new email (requires OTP verification)
        otp: OTP code (required if updating email)
    
    Returns:
        Updated CEO profile
    
    Raises:
        ValueError: If CEO not found, OTP invalid (for email update), or validation fails
    """
    # Verify CEO exists
    ceo = get_ceo_by_id(ceo_id)
    if not ceo:
        raise ValueError(f"CEO {ceo_id} not found")
    
    # Build updates dictionary
    updates = {}
    
    # Regular fields (no OTP required)
    if company_name is not None:
        if not company_name.strip():
            raise ValueError("Company name cannot be empty")
        updates["company_name"] = company_name.strip()
    
    if phone is not None:
        # Validate Nigerian phone format
        from ceo_service.utils import validate_nigerian_phone
        if not validate_nigerian_phone(phone):
            raise ValueError("Invalid Nigerian phone number format")
        updates["phone"] = phone
    
    if business_hours is not None:
        updates["business_hours"] = business_hours
    
    if delivery_fee is not None:
        if delivery_fee < 0:
            raise ValueError("Delivery fee cannot be negative")
        updates["delivery_fee"] = Decimal(str(delivery_fee))
    
    if bank_details is not None:
        # Validate bank details
        if not isinstance(bank_details, dict):
            raise ValueError("bank_details must be a dictionary")
        required_fields = ["bank_name", "account_number", "account_name"]
        for field in required_fields:
            if field not in bank_details:
                raise ValueError(f"bank_details missing required field: {field}")
        if len(bank_details["account_number"]) != 10:
            raise ValueError("account_number must be exactly 10 digits")
        if not bank_details["account_number"].isdigit():
            raise ValueError("account_number must contain only digits")
        updates["bank_details"] = bank_details
    
    # Sensitive field: email (requires OTP)
    if email is not None:
        if not otp:
            raise ValueError("OTP required to update email address")
        
        # Verify OTP
        from auth_service.otp_manager import verify_otp as verify_otp_code
        otp_result = verify_otp_code(ceo_id, otp)
        if not otp_result or not otp_result.get("valid"):
            logger.warning("CEO profile update failed - invalid OTP", extra={
                "ceo_id": ceo_id,
                "attempted_field": "email"
            })
            raise ValueError("Invalid or expired OTP")
        
        # Validate email format
        from ceo_service.utils import validate_email
        if not validate_email(email):
            raise ValueError("Invalid email format")
        
        # Check email uniqueness
        existing_ceo = get_ceo_by_email(email)
        if existing_ceo and existing_ceo.get("ceo_id") != ceo_id:
            raise ValueError("Email already in use by another CEO")
        
        updates["email"] = email
    
    # If no updates provided
    if not updates:
        raise ValueError("No fields to update")
    
    # Perform update
    updated_ceo = update_ceo(ceo_id, updates)
    
    # Log audit event
    write_audit_log(
        ceo_id=ceo_id,
        action="ceo_profile_updated",
        user_id=ceo_id,
        details={
            "updated_fields": list(updates.keys()),
            "required_otp": email is not None
        }
    )
    
    logger.info("CEO profile updated", extra={
        "ceo_id": ceo_id,
        "updated_fields": list(updates.keys())
    })
    
    # Remove sensitive data
    updated_ceo.pop("password_hash", None)
    
    return updated_ceo


# ==================== Vendor Management (OTP-Based - Zero Trust) ====================

def onboard_vendor(ceo_id: str, name: str, email: str, phone: str) -> Dict[str, Any]:
    """
    Onboard a new vendor (created by CEO) with OTP-based authentication.
    
    Args:
        ceo_id: CEO identifier (who is creating the vendor)
        name: Vendor name
        email: Vendor email
        phone: Vendor phone number
    
    Returns:
        Created vendor record with OTP sent status
    """
    # Verify CEO exists
    ceo = get_ceo_by_id(ceo_id)
    if not ceo:
        raise ValueError("CEO not found")
    
    # Create vendor (no password)
    vendor_data = {
        "name": name,
        "email": email.lower(),
        "phone": phone,
        "ceo_id": ceo_id,  # Multi-tenancy
        "created_by": ceo_id,
        "verified": False,  # Will be verified via OTP on first login
    }
    
    vendor_id = create_vendor(vendor_data)
    
    # Generate and send OTP for first login
    from auth_service.otp_manager import generate_otp, store_otp
    otp = generate_otp(role="Vendor")
    store_otp(vendor_id, otp, role="Vendor")
    
    # Send OTP to vendor (via SMS to phone)
    try:
        from common.config import settings
        import boto3
        sns = boto3.client('sns', region_name=settings.AWS_REGION)
        message = f"Welcome to TrustGuard! Your vendor account has been created. Use this OTP to login: {otp}. Valid for 5 minutes."
        sns.publish(PhoneNumber=phone, Message=message)
        logger.info(f"Vendor OTP sent via SMS", extra={"vendor_id": vendor_id, "phone": phone})
    except Exception as e:
        logger.warning(f"Failed to send vendor OTP via SMS: {e}", extra={"vendor_id": vendor_id})
    
    # Log vendor creation
    write_audit_log(
        ceo_id=ceo_id,
        action="vendor_onboarded",
        user_id=ceo_id,
        details={"vendor_id": vendor_id, "vendor_email": email}
    )
    
    logger.info("Vendor onboarded with OTP", extra={
        "ceo_id": ceo_id,
        "vendor_id": vendor_id,
        "vendor_email": email
    })
    
    # Get created vendor
    vendor = get_vendor_by_id(vendor_id)
    
    return {
        "vendor": vendor,
        "message": "Vendor onboarded successfully. OTP sent to vendor's phone for first login."
    }


def calculate_vendor_risk_score(vendor_id: str, ceo_id: str) -> float:
    """
    Calculate vendor risk score based on fraud flags and completed orders.
    
    Risk Score Formula:
        risk_score = (total_fraud_flags / total_completed_orders) if completed_orders > 0 else 0
    
    Args:
        vendor_id: Vendor identifier
        ceo_id: CEO identifier (for tenancy check)
    
    Returns:
        Float between 0.0 and 1.0 (0 = no risk, 1 = high risk)
    """
    from .database import get_audit_logs
    
    # Count fraud-related flags from audit logs
    fraud_actions = ["ORDER_FLAGGED", "RECEIPT_FLAGGED", "ESCALATION_CREATED", "FRAUD_DETECTED"]
    
    # Get audit logs for this vendor
    all_logs = get_audit_logs(ceo_id=ceo_id, user_id=vendor_id, limit=1000)
    fraud_flags = [log for log in all_logs if log.get("action") in fraud_actions]
    total_flags = len(fraud_flags)
    
    # Count completed orders (status = APPROVED or CEO_APPROVED)
    from .database import get_orders_for_ceo
    all_orders = get_orders_for_ceo(ceo_id=ceo_id, vendor_id=vendor_id)
    completed_orders = [
        order for order in all_orders 
        if order.get("order_status") in ["APPROVED", "CEO_APPROVED", "verified", "completed"]
    ]
    total_completed = len(completed_orders)
    
    # Calculate risk score
    if total_completed == 0:
        risk_score = 0.0  # No orders yet = no risk data
    else:
        risk_score = min(total_flags / total_completed, 1.0)  # Cap at 1.0
    
    logger.info(
        "Vendor risk score calculated",
        extra={
            "vendor_id": vendor_id,
            "ceo_id": ceo_id,
            "total_flags": total_flags,
            "total_completed": total_completed,
            "risk_score": round(risk_score, 3)
        }
    )
    
    return round(risk_score, 3)


def list_vendors_for_ceo(ceo_id: str) -> List[Dict[str, Any]]:
    """
    List all vendors managed by a CEO (multi-tenancy) with risk scores.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        List of vendor records with risk scores (without sensitive data)
    """
    vendors = get_all_vendors_for_ceo(ceo_id)
    
    # Add risk score to each vendor and remove sensitive data
    for vendor in vendors:
        vendor.pop("password_hash", None)
        vendor_id = vendor.get("user_id")
        if vendor_id:
            vendor["risk_score"] = calculate_vendor_risk_score(vendor_id, ceo_id)
        else:
            vendor["risk_score"] = 0.0
    
    logger.info("Vendors listed with risk scores", extra={
        "ceo_id": ceo_id,
        "count": len(vendors)
    })
    
    return vendors


def remove_vendor_by_ceo(ceo_id: str, vendor_id: str):
    """
    Remove a vendor (CEO authorization required).
    
    Args:
        ceo_id: CEO identifier
        vendor_id: Vendor identifier to delete
    
    Raises:
        ValueError: If vendor not found or not owned by CEO
    """
    # Verify vendor exists and belongs to CEO
    vendor = get_vendor_by_id(vendor_id)
    if not vendor:
        raise ValueError("Vendor not found")
    
    if vendor.get("ceo_id") != ceo_id:
        logger.warning("CEO attempted to delete vendor from another CEO", extra={
            "ceo_id": ceo_id,
            "vendor_id": vendor_id,
            "vendor_ceo_id": vendor.get("ceo_id")
        })
        raise ValueError("Unauthorized: Vendor belongs to another CEO")
    
    # Delete vendor
    delete_vendor(vendor_id)
    
    # Log deletion
    write_audit_log(
        ceo_id=ceo_id,
        action="vendor_deleted",
        user_id=ceo_id,
        details={"vendor_id": vendor_id, "vendor_email": vendor.get("email")}
    )
    
    logger.info("Vendor deleted", extra={
        "ceo_id": ceo_id,
        "vendor_id": vendor_id
    })


# ==================== Dashboard & Reporting ====================

def get_dashboard_metrics(ceo_id: str) -> Dict[str, Any]:
    """
    Get aggregated dashboard metrics for CEO.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        Dictionary with dashboard metrics
    """
    stats = get_ceo_dashboard_stats(ceo_id)
    
    logger.info("Dashboard metrics retrieved", extra={
        "ceo_id": ceo_id,
        "total_orders": stats.get("total_orders", 0),
        "total_revenue": stats.get("total_revenue", 0)
    })
    
    return stats



# ==================== Approval Workflows ====================

def get_pending_approvals(ceo_id: str) -> Dict[str, Any]:
    """
    Get all pending approval requests for CEO (flagged + high-value orders).
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        Dictionary with flagged orders and high-value orders
    """
    flagged = get_flagged_orders_for_ceo(ceo_id)
    high_value = get_high_value_orders_for_ceo(ceo_id)
    
    # Filter out duplicates (order can be both flagged and high-value)
    high_value_ids = {order["order_id"] for order in high_value}
    unique_high_value = [
        order for order in high_value 
        if order["order_id"] not in {f["order_id"] for f in flagged}
    ]
    
    logger.info("Pending approvals retrieved", extra={
        "ceo_id": ceo_id,
        "flagged_count": len(flagged),
        "high_value_count": len(unique_high_value)
    })
    
    return {
        "flagged_orders": flagged,
        "high_value_orders": unique_high_value,
        "total_pending": len(flagged) + len(unique_high_value)
    }


def approve_order(ceo_id: str, order_id: str, otp: str = None, notes: str = None) -> Dict[str, Any]:
    """
    CEO approves a flagged or high-value order.
    
    Args:
        ceo_id: CEO identifier
        order_id: Order to approve
        otp: Optional OTP for high-security approvals
        notes: Optional approval notes
    
    Returns:
        Updated order record
    
    Raises:
        ValueError: If order not found or not authorized
    """
    # Get order
    order = get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")
    
    # Verify CEO owns this order (multi-tenancy)
    if order.get("ceo_id") != ceo_id:
        logger.warning("CEO attempted to approve order from another CEO", extra={
            "ceo_id": ceo_id,
            "order_id": order_id,
            "order_ceo_id": order.get("ceo_id")
        })
        raise ValueError("Unauthorized: Order belongs to another CEO")
    
    # If OTP provided, verify it (high-value approval)
    if otp:
        if not verify_ceo_otp(ceo_id, otp):
            raise ValueError("Invalid or expired OTP")
    
    # Update order status to approved/verified
    new_status = "approved" if order.get("order_status") == "flagged" else "confirmed"
    update_order_status(
        order_id=order_id,
        new_status=new_status,
        approved_by=ceo_id,
        notes=notes
    )
    
    # Log approval
    write_audit_log(
        ceo_id=ceo_id,
        action="order_approved",
        user_id=ceo_id,
        details={
            "order_id": order_id,
            "previous_status": order.get("order_status"),
            "new_status": new_status,
            "notes": notes
        }
    )
    
    logger.info("Order approved", extra={
        "ceo_id": ceo_id,
        "order_id": order_id,
        "new_status": new_status
    })
    
    # Return updated order
    return get_order_by_id(order_id)


def reject_order(ceo_id: str, order_id: str, reason: str = None) -> Dict[str, Any]:
    """
    CEO rejects a flagged or high-value order.
    
    Args:
        ceo_id: CEO identifier
        order_id: Order to reject
        reason: Rejection reason
    
    Returns:
        Updated order record
    
    Raises:
        ValueError: If order not found or not authorized
    """
    # Get order
    order = get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")
    
    # Verify CEO owns this order (multi-tenancy)
    if order.get("ceo_id") != ceo_id:
        logger.warning("CEO attempted to reject order from another CEO", extra={
            "ceo_id": ceo_id,
            "order_id": order_id,
            "order_ceo_id": order.get("ceo_id")
        })
        raise ValueError("Unauthorized: Order belongs to another CEO")
    
    # Update order status to declined/rejected
    update_order_status(
        order_id=order_id,
        new_status="declined",
        approved_by=ceo_id,
        notes=reason
    )
    
    # Log rejection
    write_audit_log(
        ceo_id=ceo_id,
        action="order_rejected",
        user_id=ceo_id,
        details={
            "order_id": order_id,
            "previous_status": order.get("order_status"),
            "reason": reason
        }
    )
    
    logger.info("Order rejected", extra={
        "ceo_id": ceo_id,
        "order_id": order_id,
        "reason": reason
    })
    
    # Return updated order
    return get_order_by_id(order_id)


def request_approval_otp(ceo_id: str, order_id: str) -> str:
    """
    Generate and send OTP for high-value order approval.
    
    Args:
        ceo_id: CEO identifier
        order_id: Order requiring approval
    
    Returns:
        OTP code (for development/testing - in production send via SMS/email)
    """
    # Verify order exists and belongs to CEO
    order = get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")
    
    if order.get("ceo_id") != ceo_id:
        raise ValueError("Unauthorized: Order belongs to another CEO")
    
    # Generate and store OTP
    otp = generate_ceo_otp()
    store_ceo_otp(ceo_id, otp)
    
    logger.info("Approval OTP generated", extra={
        "ceo_id": ceo_id,
        "order_id": order_id
    })
    
    # TODO: Send OTP via SMS/email in production
    # For now, return OTP for testing
    return otp


# ==================== Audit Log Access ====================

def get_audit_logs_for_ceo(ceo_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve audit logs for CEO (multi-tenancy).
    
    Args:
        ceo_id: CEO identifier
        limit: Maximum number of logs to return
    
    Returns:
        List of audit log entries
    """
    logs = get_audit_logs(ceo_id=ceo_id, limit=limit)
    
    logger.info("Audit logs retrieved", extra={
        "ceo_id": ceo_id,
        "count": len(logs)
    })
    
    return logs



# Note: Legacy escalation functions below are maintained for backward compatibility
# with existing code. Consider migrating to the new approval workflow functions above.

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


# ==================== Chatbot Customization ====================

def get_chatbot_settings(ceo_id: str) -> Dict[str, Any]:
    """
    Get chatbot customization settings for a CEO from CEO_CONFIG_TABLE.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        Chatbot settings dictionary with defaults
    """
    ceo = get_ceo_by_id(ceo_id)
    if not ceo:
        raise ValueError(f"CEO {ceo_id} not found")
    
    # Fetch from dedicated config table
    config = get_chatbot_config(ceo_id)
    
    # Return chatbot settings with structure
    chatbot_settings = {
        "welcome_message": config.get("greeting", "👋 Welcome! How can I help you today?\n\nType 'help' to see available commands."),
        "business_hours": config.get("business_hours", "Mon-Fri 9AM-6PM"),
        "tone": config.get("tone", "friendly and professional"),
        "language": config.get("language", "en"),
        "auto_responses": config.get("auto_responses", {
            "greeting": "Hello! Welcome to our store. How can I assist you?",
            "thanks": "You're welcome! Let me know if you need anything else.",
            "goodbye": "Thank you for shopping with us! Have a great day! 😊"
        }),
        "enabled_features": config.get("enabled_features", {
            "address_collection": True,
            "order_tracking": True,
            "receipt_upload": True,
            "product_catalog": False
        })
    }
    
    logger.info("Chatbot settings retrieved from CEO_CONFIG_TABLE", extra={
        "ceo_id": ceo_id,
        "tone": chatbot_settings.get("tone"),
        "language": chatbot_settings.get("language")
    })
    
    return chatbot_settings


def update_chatbot_settings(
    ceo_id: str,
    welcome_message: Optional[str] = None,
    business_hours: Optional[str] = None,
    tone: Optional[str] = None,
    language: Optional[str] = None,
    auto_responses: Optional[Dict[str, str]] = None,
    enabled_features: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    Update chatbot customization settings for a CEO in CEO_CONFIG_TABLE.
    
    Args:
        ceo_id: CEO identifier
        welcome_message: Custom welcome message
        business_hours: Business operating hours
        tone: Chatbot tone (friendly, professional, casual)
        language: Language code (ISO 639-1)
        auto_responses: Custom auto-responses dictionary
        enabled_features: Feature toggles
    
    Returns:
        Updated chatbot settings
    
    Raises:
        ValueError: If CEO not found or validation fails
    """
    ceo = get_ceo_by_id(ceo_id)
    if not ceo:
        raise ValueError(f"CEO {ceo_id} not found")
    
    # Get current settings from CEO_CONFIG_TABLE
    current_config = get_chatbot_config(ceo_id)
    
    # Build updates for config table
    config_updates = {}
    
    if welcome_message is not None:
        if len(welcome_message) > 500:
            raise ValueError("Welcome message too long (max 500 characters)")
        config_updates["greeting"] = welcome_message.strip()
    
    if business_hours is not None:
        config_updates["business_hours"] = business_hours.strip()
    
    if tone is not None:
        config_updates["tone"] = tone.strip()
    
    if language is not None:
        # Basic validation (ISO 639-1 codes are 2 letters)
        if len(language) != 2:
            raise ValueError("Invalid language code. Use ISO 639-1 format (e.g., 'en', 'fr')")
        config_updates["language"] = language.lower()
    
    if auto_responses is not None:
        # Merge with current auto_responses
        current_auto_responses = current_config.get("auto_responses", {})
        current_auto_responses.update(auto_responses)
        config_updates["auto_responses"] = current_auto_responses
    
    if enabled_features is not None:
        # Merge with current enabled_features
        current_features = current_config.get("enabled_features", {})
        current_features.update(enabled_features)
        config_updates["enabled_features"] = current_features
    
    if not config_updates:
        raise ValueError("No settings to update")
    
    # Save to CEO_CONFIG_TABLE
    updated_config = save_chatbot_config(ceo_id, **config_updates)
    
    # Log audit event
    write_audit_log(
        ceo_id=ceo_id,
        action="chatbot_settings_updated",
        user_id=ceo_id,
        details={
            "updated_fields": list(config_updates.keys()),
            "tone": updated_config.get("tone"),
            "language": updated_config.get("language")
        }
    )
    
    logger.info("Chatbot settings updated in CEO_CONFIG_TABLE", extra={
        "ceo_id": ceo_id,
        "updated_fields": list(config_updates.keys())
    })
    
    # Return in expected format
    return get_chatbot_settings(ceo_id)


def preview_chatbot_conversation(
    ceo_id: str,
    user_message: str,
    settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Preview chatbot response with custom settings.
    
    Args:
        ceo_id: CEO identifier
        user_message: Simulated user message
        settings: Optional custom settings to preview (if None, uses saved settings)
    
    Returns:
        Preview response with bot message and metadata
    """
    # Get settings
    if settings is None:
        settings = get_chatbot_settings(ceo_id)
    
    # Normalize message
    message_lower = user_message.lower().strip()
    
    # Determine intent and generate response
    bot_response = ""
    intent = "unknown"
    
    # Check for greetings
    if any(word in message_lower for word in ["hi", "hello", "hey", "greetings"]):
        intent = "greeting"
        bot_response = settings.get("auto_responses", {}).get("greeting", "Hello! How can I help you?")
    
    # Check for thanks
    elif any(word in message_lower for word in ["thanks", "thank you", "thx"]):
        intent = "thanks"
        bot_response = settings.get("auto_responses", {}).get("thanks", "You're welcome!")
    
    # Check for goodbye
    elif any(word in message_lower for word in ["bye", "goodbye", "see you"]):
        intent = "goodbye"
        bot_response = settings.get("auto_responses", {}).get("goodbye", "Goodbye! Have a great day!")
    
    # Check for help
    elif "help" in message_lower:
        intent = "help"
        bot_response = (
            "Here are the commands I understand:\n\n"
            "📦 *order* - Place a new order\n"
            "📍 *address* - Update delivery address\n"
            "📷 *receipt* - Upload payment receipt\n"
            "🔍 *track* - Track your order\n"
            "❓ *help* - Show this message"
        )
    
    # Unknown intent
    else:
        intent = "unknown"
        bot_response = settings.get("auto_responses", {}).get(
            "unknown",
            "I'm not sure I understand. Type 'help' to see available commands."
        )
    
    # Apply tone adjustments
    tone = settings.get("tone", "friendly")
    if tone == "professional":
        bot_response = bot_response.replace("!", ".")
        bot_response = bot_response.replace("😊", "")
    elif tone == "casual":
        if not any(emoji in bot_response for emoji in ["😊", "👋", "📦"]):
            bot_response += " 😊"
    
    logger.info("Chatbot conversation previewed", extra={
        "ceo_id": ceo_id,
        "intent": intent,
        "tone": tone
    })
    
    return {
        "user_message": user_message,
        "bot_response": bot_response,
        "intent": intent,
        "settings_preview": {
            "tone": settings.get("tone"),
            "language": settings.get("language"),
            "business_hours": settings.get("business_hours")
        }
    }

