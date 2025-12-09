"""
Chat relay logic for vendor-to-buyer messaging.

Enables vendors to send messages to buyers via WhatsApp/Instagram
using the CEO's Meta API tokens.
"""

from typing import Dict, Any, Optional
from common.logger import logger
from integrations.whatsapp_api import WhatsAppAPI
from integrations.instagram_api import InstagramAPI
from integrations.secrets_helper import get_meta_secrets
import time
import uuid


async def send_vendor_message_to_buyer(
    vendor_id: str,
    buyer_id: str,
    message: str,
    ceo_id: str,
    order_id: Optional[str] = None,
    vendor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send message from vendor to buyer via WhatsApp or Instagram.
    
    Args:
        vendor_id: Vendor sending the message
        buyer_id: Buyer receiving the message (wa_... or ig_...)
        message: Message text to send
        ceo_id: CEO ID for fetching Meta tokens
        order_id: Optional order ID for context
        vendor_name: Optional vendor name for attribution
    
    Returns:
        Dict with message delivery status
    """
    try:
        # Validate message
        if not message or len(message.strip()) == 0:
            raise ValueError("Message cannot be empty")
        
        if len(message) > 500:
            raise ValueError("Message too long (max 500 characters)")
        
        # Determine platform from buyer_id
        if buyer_id.startswith("wa_"):
            platform = "whatsapp"
            # Remove wa_ prefix to get phone number
            phone_number = buyer_id[3:]
        elif buyer_id.startswith("ig_"):
            platform = "instagram"
            # Remove ig_ prefix to get Instagram user ID
            instagram_user_id = buyer_id[3:]
        else:
            raise ValueError(f"Invalid buyer_id format: {buyer_id}")
        
        # Fetch CEO's Meta tokens
        meta_secrets = get_meta_secrets(ceo_id)
        
        # Format message with vendor attribution
        vendor_display = vendor_name or "Vendor"
        formatted_message = f"📨 *Message from {vendor_display}:*\n\n{message}"
        
        # Add order context if provided
        if order_id:
            formatted_message += f"\n\n_Order: {order_id}_"
        
        # Send via appropriate platform
        if platform == "whatsapp":
            # Get WhatsApp credentials
            whatsapp_token = meta_secrets.get("WHATSAPP_ACCESS_TOKEN")
            whatsapp_phone_id = meta_secrets.get("WHATSAPP_PHONE_NUMBER_ID")
            
            if not whatsapp_token or not whatsapp_phone_id:
                raise ValueError("WhatsApp credentials not configured for this CEO")
            
            # Initialize WhatsApp API
            whatsapp = WhatsAppAPI(
                access_token=whatsapp_token,
                phone_number_id=whatsapp_phone_id
            )
            
            # Send message
            result = await whatsapp.send_message(phone_number, formatted_message)
            
            logger.info(
                "Vendor message sent via WhatsApp",
                extra={
                    "vendor_id": vendor_id,
                    "buyer_id": buyer_id,
                    "order_id": order_id,
                    "message_id": result.get("message_id")
                }
            )
            
            return {
                "platform": "whatsapp",
                "message_id": result.get("message_id"),
                "status": "sent",
                "sent_at": int(time.time())
            }
        
        else:  # Instagram
            # Get Instagram credentials
            instagram_token = meta_secrets.get("INSTAGRAM_ACCESS_TOKEN")
            instagram_page_id = meta_secrets.get("INSTAGRAM_PAGE_ID")
            
            if not instagram_token or not instagram_page_id:
                raise ValueError("Instagram credentials not configured for this CEO")
            
            # Initialize Instagram API
            instagram = InstagramAPI(
                access_token=instagram_token,
                page_id=instagram_page_id
            )
            
            # Send message
            result = await instagram.send_message(instagram_user_id, formatted_message)
            
            logger.info(
                "Vendor message sent via Instagram",
                extra={
                    "vendor_id": vendor_id,
                    "buyer_id": buyer_id,
                    "order_id": order_id,
                    "message_id": result.get("message_id")
                }
            )
            
            return {
                "platform": "instagram",
                "message_id": result.get("message_id"),
                "status": "sent",
                "sent_at": int(time.time())
            }
    
    except Exception as e:
        logger.error(
            f"Failed to send vendor message: {str(e)}",
            extra={
                "vendor_id": vendor_id,
                "buyer_id": buyer_id,
                "platform": platform if 'platform' in locals() else 'unknown'
            }
        )
        raise


def validate_buyer_belongs_to_ceo(buyer_id: str, ceo_id: str) -> bool:
    """
    Verify that buyer belongs to the same CEO as the vendor.
    
    Args:
        buyer_id: Buyer ID to check
        ceo_id: CEO ID to verify against
    
    Returns:
        True if buyer belongs to CEO, False otherwise
    """
    try:
        from auth_service.database import get_buyer_by_id
        
        buyer = get_buyer_by_id(buyer_id)
        if not buyer:
            return False
        
        return buyer.get("ceo_id") == ceo_id
    
    except Exception as e:
        logger.error(f"Error validating buyer ownership: {str(e)}")
        return False


def save_vendor_message_to_audit(
    vendor_id: str,
    buyer_id: str,
    message: str,
    order_id: Optional[str],
    ceo_id: str,
    platform: str,
    message_id: str
) -> None:
    """
    Save vendor message to audit trail.
    
    Args:
        vendor_id: Vendor who sent the message
        buyer_id: Buyer who received the message
        message: Message text
        order_id: Optional order ID
        ceo_id: CEO ID
        platform: 'whatsapp' or 'instagram'
        message_id: Meta message ID
    """
    try:
        from ceo_service.database import write_audit_log
        
        write_audit_log(
            ceo_id=ceo_id,
            action="vendor_message_sent",
            user_id=vendor_id,
            details={
                "buyer_id": buyer_id,
                "order_id": order_id,
                "platform": platform,
                "message_id": message_id,
                "message_length": len(message),
                "timestamp": int(time.time())
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to save message to audit log: {str(e)}")
        # Don't raise - audit logging failure shouldn't block message sending
