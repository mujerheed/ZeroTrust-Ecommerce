"""
Business logic for CEO operations.
"""

import time
import secrets
import random
import string
from typing import Dict, Any, List
from .database import (
    get_all_vendors, get_vendor_by_id, create_vendor, delete_vendor,
    get_flagged_transactions, update_order_status, get_audit_logs
)
from auth_service.database import save_otp, get_otp, delete_otp

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
