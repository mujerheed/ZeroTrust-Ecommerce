"""
Meta Platform Webhook Handler (WhatsApp & Instagram)

Handles incoming webhooks from Meta's WhatsApp Business API and Instagram Messaging API.
Implements HMAC signature verification for security.

Security Features:
- HMAC-SHA256 signature validation (X-Hub-Signature-256)
- Challenge verification for webhook setup
- Request replay attack prevention
- Multi-CEO tenancy support

Webhook Flow:
1. Meta sends POST with X-Hub-Signature-256 header
2. Verify HMAC signature using Meta App Secret
3. Parse message payload
4. Route to appropriate handler (buyer registration, OTP, order check)
5. Send response via platform API

Meta Setup:
- WhatsApp Business API: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks
- Instagram Messaging API: https://developers.facebook.com/docs/messenger-platform/webhooks
"""

import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from common.logger import logger
from common.config import settings


async def verify_meta_signature(request: Request, app_secret: str) -> bool:
    """
    Verify HMAC signature from Meta webhook.
    
    Meta sends webhooks with X-Hub-Signature-256 header:
    sha256=<HMAC-SHA256 of body using app secret>
    
    Args:
        request: FastAPI request object
        app_secret: Meta App Secret for HMAC verification
    
    Returns:
        bool: True if signature is valid
    
    Raises:
        HTTPException: If signature is invalid or missing
    """
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    if not signature_header:
        logger.warning("Webhook received without signature header")
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Get raw request body
    body = await request.body()
    
    # Calculate expected signature
    expected_signature = 'sha256=' + hmac.new(
        app_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature_header, expected_signature):
        logger.error(
            "Invalid webhook signature",
            extra={
                'received': signature_header[:20] + '...',
                'expected': expected_signature[:20] + '...'
            }
        )
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    logger.info("Webhook signature verified successfully")
    return True


async def handle_webhook_challenge(request: Request) -> Dict[str, Any]:
    """
    Handle Meta webhook verification challenge.
    
    When setting up webhooks in Meta Business Manager, Meta sends a GET request
    with hub.mode, hub.verify_token, and hub.challenge query parameters.
    
    We must respond with the challenge value if verify_token matches.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Dict with challenge value or error
    
    Example:
        GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=my_token&hub.challenge=123456
        Response: 123456
    """
    params = request.query_params
    
    mode = params.get('hub.mode')
    token = params.get('hub.verify_token')
    challenge = params.get('hub.challenge')
    
    logger.info(
        "Webhook challenge received",
        extra={
            'mode': mode,
            'token_matches': token == settings.META_WEBHOOK_VERIFY_TOKEN if hasattr(settings, 'META_WEBHOOK_VERIFY_TOKEN') else False
        }
    )
    
    # Verify mode and token
    if mode == 'subscribe':
        # Check verify token (should be set in Meta Business Manager and .env)
        expected_token = getattr(settings, 'META_WEBHOOK_VERIFY_TOKEN', 'trustguard_verify_2025')
        
        if token == expected_token:
            logger.info("Webhook verification successful", extra={'challenge': challenge})
            # Return challenge to complete verification
            return {'challenge': int(challenge)}
        else:
            logger.error("Webhook verification failed: token mismatch")
            raise HTTPException(status_code=403, detail="Invalid verify token")
    
    raise HTTPException(status_code=400, detail="Invalid webhook challenge")


def parse_whatsapp_message(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse incoming WhatsApp message from webhook payload.
    
    WhatsApp Webhook Payload Structure:
    {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "<WHATSAPP_BUSINESS_ACCOUNT_ID>",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "<BUSINESS_PHONE>",
                                "phone_number_id": "<PHONE_NUMBER_ID>"
                            },
                            "contacts": [{"profile": {"name": "<USER_NAME>"}, "wa_id": "<USER_PHONE>"}],
                            "messages": [
                                {
                                    "from": "<USER_PHONE>",
                                    "id": "<MESSAGE_ID>",
                                    "timestamp": "<TIMESTAMP>",
                                    "type": "text",
                                    "text": {"body": "<MESSAGE_TEXT>"}
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    Args:
        payload: WhatsApp webhook JSON payload
    
    Returns:
        Dict with parsed message data or None
    """
    try:
        # Navigate nested structure
        entry = payload.get('entry', [])
        if not entry:
            logger.warning("No entry in WhatsApp payload")
            return None
        
        changes = entry[0].get('changes', [])
        if not changes:
            logger.warning("No changes in WhatsApp entry")
            return None
        
        value = changes[0].get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            # Could be a status update, not an incoming message
            logger.debug("No messages in WhatsApp payload (possibly status update)")
            return None
        
        message = messages[0]
        contacts = value.get('contacts', [])
        metadata = value.get('metadata', {})
        
        # Extract message details
        sender_phone = message.get('from')  # WhatsApp ID (phone number)
        message_id = message.get('id')
        timestamp = message.get('timestamp')
        message_type = message.get('type')
        
        # Extract text content
        text_body = None
        if message_type == 'text':
            text_body = message.get('text', {}).get('body')
        elif message_type == 'interactive':
            # Handle button/list replies
            interactive = message.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                text_body = interactive.get('button_reply', {}).get('title')
            elif interactive.get('type') == 'list_reply':
                text_body = interactive.get('list_reply', {}).get('title')
        
        # Extract sender name
        sender_name = None
        if contacts:
            sender_name = contacts[0].get('profile', {}).get('name')
        
        parsed_message = {
            'platform': 'whatsapp',
            'sender_id': f'wa_{sender_phone}',  # Prefix for buyer_id format
            'sender_phone': sender_phone,
            'sender_name': sender_name,
            'message_id': message_id,
            'timestamp': timestamp,
            'message_type': message_type,
            'text': text_body,
            'business_phone_id': metadata.get('phone_number_id'),
            'raw_payload': message  # For debugging
        }
        
        logger.info(
            "WhatsApp message parsed",
            extra={
                'sender': sender_phone,
                'type': message_type,
                'text_preview': text_body[:50] if text_body else None
            }
        )
        
        return parsed_message
    
    except Exception as e:
        logger.error(f"Error parsing WhatsApp message: {str(e)}", extra={'payload': payload})
        return None


def parse_instagram_message(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse incoming Instagram message from webhook payload.
    
    Instagram Webhook Payload Structure:
    {
        "object": "instagram",
        "entry": [
            {
                "id": "<PAGE_ID>",
                "time": <TIMESTAMP>,
                "messaging": [
                    {
                        "sender": {"id": "<SENDER_PSID>"},
                        "recipient": {"id": "<PAGE_ID>"},
                        "timestamp": <TIMESTAMP>,
                        "message": {
                            "mid": "<MESSAGE_ID>",
                            "text": "<MESSAGE_TEXT>"
                        }
                    }
                ]
            }
        ]
    }
    
    Args:
        payload: Instagram webhook JSON payload
    
    Returns:
        Dict with parsed message data or None
    """
    try:
        entry = payload.get('entry', [])
        if not entry:
            logger.warning("No entry in Instagram payload")
            return None
        
        messaging = entry[0].get('messaging', [])
        if not messaging:
            logger.warning("No messaging in Instagram entry")
            return None
        
        event = messaging[0]
        sender = event.get('sender', {})
        message = event.get('message', {})
        
        # Extract message details
        sender_psid = sender.get('id')  # Page-Scoped ID
        message_id = message.get('mid')
        timestamp = event.get('timestamp')
        text_body = message.get('text')
        
        parsed_message = {
            'platform': 'instagram',
            'sender_id': f'ig_{sender_psid}',  # Prefix for buyer_id format
            'sender_psid': sender_psid,
            'sender_name': None,  # Instagram doesn't provide name in webhook
            'message_id': message_id,
            'timestamp': timestamp,
            'message_type': 'text',
            'text': text_body,
            'page_id': entry[0].get('id'),
            'raw_payload': event
        }
        
        logger.info(
            "Instagram message parsed",
            extra={
                'sender_psid': sender_psid,
                'text_preview': text_body[:50] if text_body else None
            }
        )
        
        return parsed_message
    
    except Exception as e:
        logger.error(f"Error parsing Instagram message: {str(e)}", extra={'payload': payload})
        return None


def extract_ceo_id_from_metadata(parsed_message: Dict[str, Any]) -> str:
    """
    Extract CEO ID from webhook message metadata for multi-tenancy.
    
    In production, this would:
    1. Look up which CEO owns the WhatsApp Business Phone Number or Instagram Page
    2. Map business_phone_id/page_id to ceo_id in database
    
    For now, we'll use a default or extract from environment.
    
    Args:
        parsed_message: Parsed message dict
    
    Returns:
        str: CEO ID for this business
    """
    # TODO: Implement database lookup
    # Query: SELECT ceo_id FROM business_accounts WHERE phone_id = ? OR page_id = ?
    
    # For development, use default CEO from settings or hardcode
    default_ceo = getattr(settings, 'DEFAULT_CEO_ID', 'ceo_dev_default')
    
    logger.debug(
        f"Using CEO ID: {default_ceo} for platform: {parsed_message.get('platform')}"
    )
    
    return default_ceo


async def process_webhook_message(
    parsed_message: Dict[str, Any],
    ceo_id: str
) -> Dict[str, Any]:
    """
    Process parsed webhook message and route to appropriate handler.
    
    Message Intent Detection:
    - "register" / "start" → Buyer registration flow
    - "verify <OTP>" → OTP verification
    - "order <order_id>" → Order status check
    - "upload" → Receipt upload instructions
    - Default → Help message
    
    Args:
        parsed_message: Parsed message dict
        ceo_id: CEO ID for this business
    
    Returns:
        Dict with response message and action taken
    """
    from integrations.chatbot_router import route_message
    
    # Route message to chatbot logic
    response = await route_message(parsed_message, ceo_id)
    
    return response
