"""
Instagram PSID to Phone-Based Buyer ID Mapping Helper

This module provides utilities to map Instagram PSIDs to phone-based buyer IDs
for consistent buyer identification across WhatsApp and Instagram platforms.

Format:
- WhatsApp: wa_234XXXXXXXXXX (phone-based)
- Instagram: ig_234XXXXXXXXXX (phone-based, PSID stored in meta)
"""

from auth_service.database import get_user
from common.db_connection import dynamodb
from common.config import settings
from boto3.dynamodb.conditions import Attr
from common.logger import logger


def get_buyer_by_psid(instagram_psid: str) -> dict:
    """
    Look up Instagram buyer by their original PSID.
    
    Since we now store buyers with phone-based IDs (ig_234XXXXXXXXXX),
    we need to scan the Users table to find the buyer with matching PSID in meta.
    
    Args:
        instagram_psid: Instagram Page-Scoped ID (e.g., "1234567890")
    
    Returns:
        Buyer record or None if not found
    
    Example:
        >>> buyer = get_buyer_by_psid("1234567890")
        >>> print(buyer['user_id'])  # ig_2348012345678
    """
    table = dynamodb.Table(settings.USERS_TABLE)
    
    try:
        # Scan for buyer with matching instagram_psid in meta
        response = table.scan(
            FilterExpression=Attr('meta.instagram_psid').eq(instagram_psid)
        )
        
        items = response.get('Items', [])
        
        if items:
            buyer = items[0]
            logger.info(
                f"Found buyer by PSID: {instagram_psid} → {buyer['user_id']}",
                extra={'psid': instagram_psid, 'buyer_id': buyer['user_id']}
            )
            return buyer
        
        logger.warning(f"No buyer found with PSID: {instagram_psid}")
        return None
    
    except Exception as e:
        logger.error(f"Error looking up buyer by PSID: {str(e)}")
        return None


def get_phone_based_buyer_id(sender_id: str, phone: str = None) -> str:
    """
    Convert sender_id to phone-based buyer_id format.
    
    Args:
        sender_id: Original sender ID (wa_234... or ig_PSID)
        phone: Phone number (optional, for Instagram)
    
    Returns:
        Phone-based buyer ID
    
    Examples:
        >>> get_phone_based_buyer_id("wa_2348012345678")
        "wa_2348012345678"  # Already phone-based
        
        >>> get_phone_based_buyer_id("ig_1234567890", "+2348012345678")
        "ig_2348012345678"  # Converted to phone-based
    """
    if sender_id.startswith('wa_'):
        # WhatsApp already uses phone-based IDs
        return sender_id
    
    elif sender_id.startswith('ig_'):
        # Instagram: Check if already phone-based or PSID-based
        psid_part = sender_id.replace('ig_', '')
        
        # If starts with 234 (Nigerian country code), likely phone-based
        if psid_part.startswith('234'):
            return sender_id
        
        # Otherwise, it's PSID-based - look up the phone-based ID
        buyer = get_buyer_by_psid(psid_part)
        if buyer:
            return buyer['user_id']
        
        # If not found and phone provided, create phone-based ID
        if phone:
            from auth_service.auth_logic import normalize_phone
            normalized = normalize_phone(phone)
            phone_digits = normalized.replace('+', '')
            return f"ig_{phone_digits}"
    
    # Fallback: return as-is
    return sender_id
