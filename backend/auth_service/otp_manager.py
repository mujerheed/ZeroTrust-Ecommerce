"""
OTP generation and validation.
"""

import os
import random
import string
from datetime import datetime
from database import save_otp, get_otp, delete_otp, log_event

# OTP settings
OTP_TTL_SECONDS    = 300
OTP_LENGTH_DEFAULT = 8
OTP_LENGTH_CEO     = 6

def generate_otp(role: str) -> str:
    """
    Generate an OTP based on role.
    """
    if role.upper() == "CEO":
        chars = string.digits + string.punctuation
        length = OTP_LENGTH_CEO
    else:
        chars = string.ascii_letters + string.digits + string.punctuation
        length = OTP_LENGTH_DEFAULT
    return "".join(random.choices(chars, k=length))

def request_otp(user_id: str, role: str, contact: str) -> bool:
    """
    Generate, store, and simulate sending OTP.
    """
    try:
        otp = generate_otp(role)
        save_otp(user_id, otp, role, OTP_TTL_SECONDS)
        # TODO: integrate real SMS/WhatsApp/API call here
        print(f"Simulate sending OTP {otp} to {contact}")
        log_event(user_id, "OTP_REQUEST", "SUCCESS", f"OTP sent to {contact}")
        return True
    except Exception as e:
        log_event(user_id, "OTP_REQUEST", "FAILED", str(e))
        raise

def verify_otp(user_id: str, submitted_otp: str) -> dict:
    """
    Validate an OTP, delete on success, and return role if valid.
    """
    record = get_otp(user_id)
    if not record:
        log_event(user_id, "OTP_VERIFY", "FAILED", "OTP missing or expired")
        return {"valid": False}
    if record["otp_code"] != submitted_otp:
        log_event(user_id, "OTP_VERIFY", "FAILED", "OTP mismatch")
        return {"valid": False}
    # Success
    delete_otp(user_id)
    log_event(user_id, "OTP_VERIFY", "SUCCESS", "OTP verified")
    return {"valid": True, "role": record["role"]}
