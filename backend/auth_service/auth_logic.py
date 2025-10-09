"""
Authentication business logic.
"""
from time import time
from database import get_user
from otp_manager import request_otp, verify_otp
from token_manager import create_jwt

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
