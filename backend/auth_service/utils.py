"""
Authentication Service Utility Functions

This module provides helper functions and utilities for the authentication service
including response formatting, input validation, error handling, and security helpers.

Author: TrustGuard Team
Date: October 2025
"""

import re
import json
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import secrets


def format_response(status: str, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Standardize API response format across all authentication endpoints.
    
    Args:
        status (str): Response status ('success', 'error', 'warning')
        message (str): Human-readable message describing the response
        data (Dict[str, Any], optional): Additional data payload
    
    Returns:
        Dict[str, Any]: Formatted response dictionary
    
    Example:
        format_response("success", "User registered", {"user_id": "123"})
    """
    return {
        "status": status,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }


def validate_phone_number(phone: str) -> bool:
    """
    Validate Nigerian phone number format.
    
    Accepts formats:
    - +2348012345678 (international format)
    - 08012345678 (local format)
    - 2348012345678 (country code without +)
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        bool: True if valid, raises ValueError if invalid
    
    Raises:
        ValueError: If phone number format is invalid
    """
    # Remove all non-digit characters except +
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Check for valid Nigerian phone patterns
    patterns = [
        r'^\+234[789][01]\d{8}$',  # +234 followed by valid Nigerian mobile prefixes
        r'^234[789][01]\d{8}$',   # 234 without +
        r'^0[789][01]\d{8}$'      # Local format starting with 0
    ]
    
    if not any(re.match(pattern, cleaned_phone) for pattern in patterns):
        raise ValueError("Invalid Nigerian phone number format")
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address format using regex.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid, raises ValueError if invalid
    
    Raises:
        ValueError: If email format is invalid
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email.lower()):
        raise ValueError("Invalid email address format")
    
    return True


def validate_user_name(name: str) -> bool:
    """
    Validate user name meets security requirements.
    
    Requirements:
    - Length between 2-50 characters
    - Only letters, spaces, hyphens, and apostrophes
    - No consecutive spaces
    
    Args:
        name (str): User name to validate
    
    Returns:
        bool: True if valid, raises ValueError if invalid
    
    Raises:
        ValueError: If name doesn't meet requirements
    """
    if not name or len(name.strip()) < 2:
        raise ValueError("Name must be at least 2 characters long")
    
    if len(name.strip()) > 50:
        raise ValueError("Name cannot exceed 50 characters")
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
    
    # Check for consecutive spaces
    if '  ' in name:
        raise ValueError("Name cannot contain consecutive spaces")
    
    return True


def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_string (str): String to sanitize
        max_length (int): Maximum allowed length
    
    Returns:
        str: Sanitized string
    """
    if not isinstance(input_string, str):
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', input_string)
    
    # Trim whitespace and limit length
    sanitized = sanitized.strip()[:max_length]
    
    return sanitized


def generate_user_id() -> str:
    """
    Generate a unique, secure user ID.
    
    Returns:
        str: Unique user identifier (format: user_XXXXXXXXXXXXXXXX)
    """
    # Generate 16 random bytes and encode as hex
    random_part = secrets.token_hex(8)
    return f"user_{random_part}"


def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """
    Hash sensitive data using SHA-256 with optional salt.
    
    Args:
        data (str): Data to hash
        salt (str, optional): Salt for additional security
    
    Returns:
        str: Hashed data as hexadecimal string
    """
    if salt:
        data = salt + data
    
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def log_security_event(user_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structure security events for audit logging.
    
    Args:
        user_id (str): ID of user involved in the event
        event_type (str): Type of security event (e.g., 'login_attempt', 'otp_generated')
        details (Dict[str, Any]): Additional event details
    
    Returns:
        Dict[str, Any]: Formatted security log entry
    """
    return {
        "log_id": secrets.token_hex(16),
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "event_type": event_type,
        "details": details,
        "ip_address": details.get("ip_address", "unknown"),
        "user_agent": details.get("user_agent", "unknown")
    }


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging purposes (e.g., phone numbers, emails).
    
    Args:
        data (str): Sensitive data to mask
        visible_chars (int): Number of characters to leave visible at the end
    
    Returns:
        str: Masked data string
    
    Example:
        mask_sensitive_data("08012345678", 4) returns "0801234****"
    """
    if len(data) <= visible_chars:
        return "*" * len(data)
    
    return data[:-visible_chars] + "*" * visible_chars


def validate_otp_format(otp: str) -> bool:
    """
    Validate OTP format based on Zero Trust requirements.
    
    For buyers: 8 characters (letters, digits, special chars)
    For CEO: 6 characters (digits and symbols only)
    
    Args:
        otp (str): OTP to validate
    
    Returns:
        bool: True if format is valid, False otherwise
    """
    # Check if it's 8-char buyer OTP (alphanumeric + specials)
    if len(otp) == 8:
        return bool(re.match(r'^[a-zA-Z0-9!@#$%^&*]{8}$', otp))
    
    # Check if it's 6-char CEO OTP (digits + symbols)
    elif len(otp) == 6:
        return bool(re.match(r'^[0-9!@#$%^&*]{6}$', otp))
    
    return False


def get_error_response(error_code: str, error_message: str) -> Dict[str, Any]:
    """
    Generate standardized error response format.
    
    Args:
        error_code (str): Specific error code for debugging
        error_message (str): User-friendly error message
    
    Returns:
        Dict[str, Any]: Formatted error response
    """
    return {
        "status": "error",
        "error_code": error_code,
        "message": error_message,
        "timestamp": datetime.utcnow().isoformat()
    }


def rate_limit_check(client_ip: str, action: str, max_attempts: int, window_minutes: int) -> None:
    """
    Rate limiting wrapper for backward compatibility with auth_routes.py.
    
    This function wraps the common/security.rate_limit function with a different
    signature that accepts client IP directly instead of Request object.
    
    Args:
        client_ip (str): Client IP address for rate limiting
        action (str): Action identifier (e.g., 'ceo_register', 'otp_verify')
        max_attempts (int): Maximum allowed attempts within the time window
        window_minutes (int): Time window in minutes
    
    Raises:
        HTTPException: If rate limit is exceeded (429 status code)
    
    Example:
        rate_limit_check("192.168.1.1", "ceo_login", max_attempts=5, window_minutes=15)
    """
    from fastapi import HTTPException
    from starlette.status import HTTP_429_TOO_MANY_REQUESTS
    import time
    from threading import Lock
    
    # Simple in-memory rate limiter (mirrors common/security.py implementation)
    if not hasattr(rate_limit_check, '_limits'):
        rate_limit_check._limits = {}
        rate_limit_check._lock = Lock()
    
    identifier = f"{action}:{client_ip}"
    now = int(time.time())
    period_seconds = window_minutes * 60
    window = now // period_seconds
    
    with rate_limit_check._lock:
        count = rate_limit_check._limits.get((identifier, window), 0)
        if count >= max_attempts:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many {action} attempts. Please try again later."
            )
        rate_limit_check._limits[(identifier, window)] = count + 1
