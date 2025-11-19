"""
OTP generation, validation, and delivery with Zero Trust security.

This module implements:
- Role-specific OTP formats (Buyer: 8-char, CEO: 6-char)
- Hashed OTP storage (never store plaintext)
- Platform-aware delivery priority
- Retry limits and account lockout
- DynamoDB integration with TTL
"""

import os
import random
import string
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Literal
from common.config import settings
from common.db_connection import dynamodb
from common.logger import logger

# OTP Configuration
OTP_TTL_SECONDS = 300  # 5 minutes
OTP_LENGTH_BUYER_VENDOR = 8
OTP_LENGTH_CEO = 6
MAX_OTP_ATTEMPTS = 3
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes

# Character sets for OTP generation
BUYER_VENDOR_CHARS = string.ascii_letters + string.digits + "!@#$%^&*"
CEO_CHARS = string.digits + "!@#$%^&*"


def _hash_otp(otp: str) -> str:
    """
    Hash OTP using SHA-256 for secure storage.
    
    Args:
        otp (str): Plaintext OTP
    
    Returns:
        str: SHA-256 hash of the OTP
    """
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def generate_otp(role: str) -> str:
    """
    Generate a cryptographically secure OTP based on user role.
    
    Args:
        role (str): User role ('Buyer', 'Vendor', or 'CEO')
    
    Returns:
        str: Generated OTP string
    
    Example:
        >>> generate_otp('CEO')
        '3!5@7*'
        >>> generate_otp('Buyer')
        'aB3$xY7!'
    """
    if role.upper() == "CEO":
        chars = CEO_CHARS
        length = OTP_LENGTH_CEO
    else:  # Buyer or Vendor
        chars = BUYER_VENDOR_CHARS
        length = OTP_LENGTH_BUYER_VENDOR
    
    # Use secrets module for cryptographically secure random generation
    return ''.join(secrets.choice(chars) for _ in range(length))


def _store_otp(
    user_id: str,
    otp_hash: str,
    role: str,
    delivery_method: str,
    platform: Optional[str] = None
) -> None:
    """
    Store hashed OTP in DynamoDB with TTL.
    
    Args:
        user_id (str): User identifier
        otp_hash (str): SHA-256 hash of the OTP
        role (str): User role
        delivery_method (str): Delivery channel used
        platform (str, optional): Platform for buyer (whatsapp/instagram)
    """
    table = dynamodb.Table(settings.OTPS_TABLE)
    now = int(time.time())
    
    item = {
        'user_id': user_id,
        'otp_hash': otp_hash,
        'role': role,
        'delivery_method': delivery_method,
        'attempts': 0,
        'created_at': now,
        'expires_at': now + OTP_TTL_SECONDS,  # DynamoDB TTL attribute
        'locked_until': 0
    }
    
    if platform:
        item['platform'] = platform
    
    table.put_item(Item=item)
    logger.info(f"OTP stored for user_id={user_id}, role={role}, delivery={delivery_method}")


def _get_otp_record(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve OTP record from DynamoDB.
    
    Args:
        user_id (str): User identifier
    
    Returns:
        Optional[Dict]: OTP record or None if not found/expired
    """
    table = dynamodb.Table(settings.OTPS_TABLE)
    
    try:
        response = table.get_item(Key={'user_id': user_id})
        record = response.get('Item')
        
        if not record:
            return None
        
        # Check if expired (belt-and-suspenders with DynamoDB TTL)
        if record.get('expires_at', 0) < int(time.time()):
            logger.warning(f"OTP expired for user_id={user_id}")
            return None
        
        # Check if locked out
        if record.get('locked_until', 0) > int(time.time()):
            logger.warning(f"User locked out: user_id={user_id}")
            return None
        
        return record
        
    except Exception as e:
        logger.error(f"Error retrieving OTP for user_id={user_id}: {str(e)}")
        return None


def _delete_otp(user_id: str) -> None:
    """Delete OTP record after successful verification."""
    table = dynamodb.Table(settings.OTPS_TABLE)
    table.delete_item(Key={'user_id': user_id})
    logger.info(f"OTP deleted for user_id={user_id}")


def _increment_attempts(user_id: str, current_attempts: int) -> None:
    """
    Increment OTP verification attempts and lock account if limit exceeded.
    
    Args:
        user_id (str): User identifier
        current_attempts (int): Current attempt count
    """
    table = dynamodb.Table(settings.OTPS_TABLE)
    new_attempts = current_attempts + 1
    
    update_expr = "SET attempts = :attempts"
    expr_values = {':attempts': new_attempts}
    
    # Lock account for 15 minutes after max attempts
    if new_attempts >= MAX_OTP_ATTEMPTS:
        locked_until = int(time.time()) + LOCKOUT_DURATION_SECONDS
        update_expr += ", locked_until = :locked"
        expr_values[':locked'] = locked_until
        logger.warning(f"User locked out after {MAX_OTP_ATTEMPTS} failed attempts: user_id={user_id}")
    
    table.update_item(
        Key={'user_id': user_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values
    )


def _deliver_otp_buyer(
    user_id: str,
    otp: str,
    platform: Literal['whatsapp', 'instagram'],
    phone: Optional[str] = None
) -> str:
    """
    Deliver OTP to buyer with priority: Platform DM → SMS fallback.
    
    Args:
        user_id (str): Buyer ID (format: wa_xxx or ig_xxx)
        otp (str): Plaintext OTP to deliver
        platform (str): 'whatsapp' or 'instagram'
        phone (str, optional): Phone number for SMS fallback
    
    Returns:
        str: Delivery method used ('whatsapp', 'instagram', or 'sms')
    """
    # TODO: Implement actual Meta API integration
    # For now, simulate delivery
    
    try:
        if platform == 'whatsapp':
            # TODO: Call WhatsApp Business API
            logger.info(f"[MOCK] Sending OTP via WhatsApp to {user_id}: {otp}")
            return 'whatsapp'
        elif platform == 'instagram':
            # TODO: Call Instagram Messaging API
            logger.info(f"[MOCK] Sending OTP via Instagram to {user_id}: {otp}")
            return 'instagram'
    except Exception as e:
        logger.warning(f"Platform delivery failed for {user_id}: {str(e)}, falling back to SMS")
    
    # Fallback to SMS if platform delivery fails or phone is available
    if phone:
        # TODO: Implement AWS SNS SMS delivery
        logger.info(f"[MOCK] Sending OTP via SMS to {phone}: {otp}")
        return 'sms'
    
    raise Exception(f"Failed to deliver OTP to {user_id}: no valid delivery channel")


def _deliver_otp_vendor(phone: str, otp: str) -> str:
    """
    Deliver OTP to vendor via SMS (dashboard users).
    
    Args:
        phone (str): Vendor phone number
        otp (str): Plaintext OTP to deliver
    
    Returns:
        str: Delivery method ('sms')
    """
    # TODO: Implement AWS SNS SMS delivery
    logger.info(f"[MOCK] Sending Vendor OTP via SMS to {phone}: {otp}")
    return 'sms'


def _deliver_otp_ceo(phone: str, email: str, otp: str) -> str:
    """
    Deliver OTP to CEO via SMS + Email (dual delivery for security).
    
    Args:
        phone (str): CEO phone number
        email (str): CEO email address
        otp (str): Plaintext OTP to deliver
    
    Returns:
        str: Delivery method ('sms_email')
    """
    # TODO: Implement AWS SNS for SMS and SES for Email
    logger.info(f"[MOCK] Sending CEO OTP via SMS to {phone}: {otp}")
    logger.info(f"[MOCK] Sending CEO OTP via Email to {email}: {otp}")
    return 'sms_email'


def request_otp(
    user_id: str,
    role: str,
    contact: str,
    platform: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate, store (hashed), and deliver OTP based on role and platform.
    
    Args:
        user_id (str): User identifier
        role (str): User role ('Buyer', 'Vendor', 'CEO')
        contact (str): Primary contact (phone/email)
        platform (str, optional): Platform for buyer ('whatsapp' or 'instagram')
        phone (str, optional): Phone number for SMS fallback (buyers on Instagram)
    
    Returns:
        Dict[str, Any]: Status and delivery information
    
    Raises:
        Exception: If OTP delivery fails
    """
    try:
        # Generate OTP
        otp = generate_otp(role)
        otp_hash = _hash_otp(otp)
        
        # Deliver based on role
        if role.upper() == 'BUYER':
            if not platform:
                raise ValueError("Platform required for buyer OTP delivery")
            delivery_method = _deliver_otp_buyer(user_id, otp, platform, phone)
        elif role.upper() == 'VENDOR':
            delivery_method = _deliver_otp_vendor(contact, otp)
        elif role.upper() == 'CEO':
            # Assume contact is phone, need email separately
            # For CEO, contact should be phone and we need email from user record
            delivery_method = _deliver_otp_ceo(contact, contact, otp)  # TODO: get actual email
        else:
            raise ValueError(f"Invalid role: {role}")
        
        # Store hashed OTP
        _store_otp(user_id, otp_hash, role, delivery_method, platform)
        
        # Log event to audit logs
        from database import log_event
        log_event(user_id, "OTP_REQUEST", "SUCCESS", f"OTP sent via {delivery_method}")
        
        return {
            'success': True,
            'delivery_method': delivery_method,
            'expires_in_seconds': OTP_TTL_SECONDS
        }
        
    except Exception as e:
        logger.error(f"OTP request failed for user_id={user_id}: {str(e)}")
        from database import log_event
        log_event(user_id, "OTP_REQUEST", "FAILED", str(e))
        raise


def verify_otp(user_id: str, submitted_otp: str) -> Dict[str, Any]:
    """
    Verify submitted OTP against hashed stored value.
    
    Args:
        user_id (str): User identifier
        submitted_otp (str): OTP submitted by user
    
    Returns:
        Dict[str, Any]: Verification result with role if successful
    
    Example:
        >>> verify_otp('wa_1234567890', 'aB3$xY7!')
        {'valid': True, 'role': 'Buyer'}
    """
    from database import log_event
    
    # Retrieve OTP record
    record = _get_otp_record(user_id)
    
    if not record:
        log_event(user_id, "OTP_VERIFY", "FAILED", "OTP not found or expired")
        return {'valid': False, 'error': 'OTP expired or not found'}
    
    # Check if account is locked
    if record.get('locked_until', 0) > int(time.time()):
        remaining = record['locked_until'] - int(time.time())
        log_event(user_id, "OTP_VERIFY", "BLOCKED", f"Account locked, {remaining}s remaining")
        return {
            'valid': False,
            'error': f'Account locked. Try again in {remaining // 60} minutes'
        }
    
    # Hash submitted OTP and compare
    submitted_hash = _hash_otp(submitted_otp)
    
    if submitted_hash != record['otp_hash']:
        # Increment attempts
        _increment_attempts(user_id, record.get('attempts', 0))
        log_event(user_id, "OTP_VERIFY", "FAILED", "OTP mismatch")
        
        attempts_left = MAX_OTP_ATTEMPTS - record.get('attempts', 0) - 1
        return {
            'valid': False,
            'error': f'Invalid OTP. {max(0, attempts_left)} attempts remaining'
        }
    
    # Success: delete OTP record
    _delete_otp(user_id)
    log_event(user_id, "OTP_VERIFY", "SUCCESS", "OTP verified")
    
    return {
        'valid': True,
        'role': record['role']
    }


def store_otp(
    user_id: str,
    otp_hash: str,
    role: str,
    delivery_method: str,
    platform: Optional[str] = None
) -> None:
    """
    Public wrapper for _store_otp to allow direct OTP storage.
    Used by chatbot_router for buyer authentication flows.
    
    Args:
        user_id (str): User identifier
        otp_hash (str): SHA-256 hash of the OTP
        role (str): User role
        delivery_method (str): Delivery channel used
        platform (str, optional): Platform for buyer (whatsapp/instagram)
    """
    _store_otp(user_id, otp_hash, role, delivery_method, platform)


def hash_otp(otp: str) -> str:
    """
    Public wrapper for _hash_otp to allow external hashing.
    Used when OTP needs to be hashed before storage.
    
    Args:
        otp (str): Plaintext OTP
    
    Returns:
        str: SHA-256 hash of the OTP
    """
    return _hash_otp(otp)
