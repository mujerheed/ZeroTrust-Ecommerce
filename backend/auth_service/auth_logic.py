"""
Authentication business logic.
"""
from time import time
from .database import get_user
from .otp_manager import request_otp, verify_otp
from .token_manager import create_jwt


def register_ceo(name: str, phone: str, email: str) -> dict:
    """
    Register a new CEO (self-registration).
    Returns user_id for OTP verification.
    """
    # TODO: Create CEO in DynamoDB USERS_TABLE
    ceo_id = f"ceo_{int(time() * 1000)}"
    # Mock implementation - in production, save to DynamoDB
    return {"ceo_id": ceo_id, "status": "pending_verification"}


def login_ceo(phone: str) -> dict:
    """
    Initiate CEO login via OTP.
    """
    # TODO: Fetch CEO by phone from DynamoDB
    # For now, mock response
    return {"status": "otp_sent", "message": "OTP sent to your phone"}


def login_vendor(phone: str) -> dict:
    """
    Initiate vendor login via OTP.
    """
    # TODO: Fetch vendor by phone from DynamoDB
    return {"status": "otp_sent", "message": "OTP sent to your phone"}


def verify_otp_universal(user_id: str, otp: str, role: str) -> dict:
    """
    Universal OTP verification for all user types.
    Returns JWT token if valid.
    """
    result = verify_otp(user_id, otp)
    if not result.get("valid"):
        return {"valid": False, "message": "Invalid or expired OTP"}
    
    # Generate JWT token
    token = create_jwt(user_id, role)
    return {"valid": True, "token": token, "role": role}


def create_vendor_account(name: str, phone: str, email: str, created_by: str) -> str:
    """
    CEO creates a vendor account.
    Returns vendor_id.
    """
    # TODO: Create vendor in DynamoDB USERS_TABLE
    vendor_id = f"vendor_{int(time() * 1000)}"
    # Mock implementation - in production, save to DynamoDB with created_by (ceo_id)
    return vendor_id


def register_user(email: str, phone: str, name: str) -> str:
    """
    (Optional) Implement user creation in USERS_TABLE.
    """
    # TODO: add to DynamoDB users table
    user_id = f"user_{int(time.time())}"
    return user_id  # return the new user_id

def login_user(user_id: str) -> bool:
    """
    Initiate OTP process for login.
    """
    user = get_user(user_id)
    if not user:
        raise Exception("User not found")
    contact = user.get("contact") or user.get("email")
    return request_otp(user_id, user.get("role", "Buyer"), contact)

def verify_otp_code(user_id: str, otp: str) -> str:
    """
    Verify OTP and return a JWT if successful.
    """
    result = verify_otp(user_id, otp)
    if not result.get("valid"):
        raise Exception("Invalid or expired OTP")
    return create_jwt(user_id, result["role"])
