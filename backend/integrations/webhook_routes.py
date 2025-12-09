"""
Meta Platform Webhook Routes (WhatsApp & Instagram)

Provides FastAPI endpoints for receiving and processing webhooks from Meta.

Endpoints:
- GET/POST /integrations/webhook/whatsapp - WhatsApp Business API webhook
- GET/POST /integrations/webhook/instagram - Instagram Messaging API webhook
- GET /integrations/health - Health check for webhook endpoint
"""

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any
import json

from common.logger import logger
from common.config import settings
from .webhook_handler import (
    verify_meta_signature,
    handle_webhook_challenge,
    parse_whatsapp_message,
    parse_instagram_message
)
from .chatbot_router import ChatbotRouter
from .secrets_helper import get_meta_secrets


router = APIRouter()
chatbot = ChatbotRouter()


@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    WhatsApp webhook verification endpoint (GET).
    
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    when you first set up the webhook in Meta Business Manager.
    
    Example:
        GET /integrations/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=trustguard_verify_2025&hub.challenge=123456
    
    Returns:
        Plain text challenge value if verification succeeds
    """
    try:
        result = await handle_webhook_challenge(request)
        challenge = result.get('challenge')
        
        logger.info("WhatsApp webhook verified successfully", extra={'challenge': challenge})
        
        # Return challenge as plain text (not JSON)
        return PlainTextResponse(content=str(challenge))
    
    except HTTPException as e:
        logger.error(f"WhatsApp webhook verification failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"WhatsApp webhook verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook_receive(request: Request):
    """
    WhatsApp webhook message receiver (POST).
    
    Receives incoming messages from WhatsApp Business API, verifies signature,
    parses message, and routes to chatbot handler.
    
    Security:
        - IP allowlisting (Meta's official webhook servers)
        - Validates HMAC signature (X-Hub-Signature-256)
        - Replay attack prevention (timestamp + message ID deduplication)
        - Uses Meta App Secret from Secrets Manager
    
    Returns:
        200 OK to acknowledge receipt (Meta expects this within 20 seconds)
    """
    # VISIBLE CONSOLE LOGGING
    print("\n" + "="*80)
    print("🔔 WHATSAPP WEBHOOK RECEIVED!")
    print("="*80 + "\n")
    
    try:
        # 1. IP Allowlisting (optional but recommended for production)
        from .ip_allowlist import get_client_ip, is_ip_allowed
        from .webhook_handler import META_WEBHOOK_IPS
        
        client_ip = get_client_ip(request)
        
        # Skip IP check in dev mode or if IP is unknown (local testing)
        if settings.ENVIRONMENT == "production" and client_ip != "unknown":
            if not is_ip_allowed(client_ip, META_WEBHOOK_IPS):
                logger.warning(
                    f"Webhook request from unauthorized IP: {client_ip}",
                    extra={'client_ip': client_ip}
                )
                raise HTTPException(
                    status_code=403,
                    detail="Unauthorized IP address"
                )
        
        # 2. Get Meta App Secret for signature verification
        secrets = await get_meta_secrets()
        app_secret = secrets.get('APP_SECRET')
        
        if not app_secret:
            logger.error("Meta App Secret not found in Secrets Manager")
            # Still return 200 to Meta to avoid retries, but don't process
            return JSONResponse(content={"status": "error", "message": "Configuration error"}, status_code=200)
        
        # 3. Verify HMAC signature + replay attack prevention
        await verify_meta_signature(request, app_secret)
        
        # Parse request body
        body = await request.json()
        
        logger.info("WhatsApp webhook received", extra={'object': body.get('object')})
        
        # Check if this is a WhatsApp Business Account webhook
        if body.get('object') != 'whatsapp_business_account':
            logger.warning(f"Unexpected webhook object type: {body.get('object')}")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Parse message
        parsed_message = parse_whatsapp_message(body)
        
        if not parsed_message:
            logger.info("No processable message in WhatsApp webhook (possibly status update)")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Route to chatbot handler (async, non-blocking)
        try:
            await chatbot.handle_message(parsed_message)
        except Exception as e:
            # Log error but still return 200 to Meta
            logger.error(f"Error processing WhatsApp message: {str(e)}", exc_info=True)
        
        # Always return 200 OK to Meta within 20 seconds
        return JSONResponse(content={"status": "received"}, status_code=200)
    
    except HTTPException:
        # Signature verification failed - return error
        raise
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}", exc_info=True)
        # Return 200 to prevent Meta retries
        return JSONResponse(content={"status": "error"}, status_code=200)


@router.get("/webhook/instagram")
async def instagram_webhook_verify(request: Request):
    """
    Instagram webhook verification endpoint (GET).
    
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    when you first set up the webhook in Meta Business Manager.
    
    Example:
        GET /integrations/webhook/instagram?hub.mode=subscribe&hub.verify_token=trustguard_verify_2025&hub.challenge=123456
    
    Returns:
        Plain text challenge value if verification succeeds
    """
    try:
        result = await handle_webhook_challenge(request)
        challenge = result.get('challenge')
        
        logger.info("Instagram webhook verified successfully", extra={'challenge': challenge})
        
        # Return challenge as plain text (not JSON)
        return PlainTextResponse(content=str(challenge))
    
    except HTTPException as e:
        logger.error(f"Instagram webhook verification failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Instagram webhook verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook verification failed")


@router.post("/webhook/instagram")
async def instagram_webhook_receive(request: Request):
    """
    Instagram webhook message receiver (POST).
    
    Receives incoming messages from Instagram Messaging API, verifies signature,
    parses message, and routes to chatbot handler.
    
    Security:
        - Validates HMAC signature (X-Hub-Signature-256)
        - Uses Meta App Secret from Secrets Manager
    
    Returns:
        200 OK to acknowledge receipt (Meta expects this within 20 seconds)
    """
    # VISIBLE CONSOLE LOGGING
    print("\n" + "="*80)
    print("📸 INSTAGRAM WEBHOOK RECEIVED!")
    print("="*80 + "\n")
    
    try:
        # Get Meta App Secret for signature verification
        secrets = await get_meta_secrets()
        app_secret = secrets.get('APP_SECRET')
        
        if not app_secret:
            logger.error("Meta App Secret not found in Secrets Manager")
            # Still return 200 to Meta to avoid retries, but don't process
            return JSONResponse(content={"status": "error", "message": "Configuration error"}, status_code=200)
        
        # Verify HMAC signature
        await verify_meta_signature(request, app_secret)
        
        # Parse request body
        body = await request.json()
        
        logger.info("Instagram webhook received", extra={'object': body.get('object')})
        
        # Check if this is an Instagram webhook
        if body.get('object') != 'instagram':
            logger.warning(f"Unexpected webhook object type: {body.get('object')}")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Parse message
        parsed_message = parse_instagram_message(body)
        
        if not parsed_message:
            logger.info("No processable message in Instagram webhook")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Route to chatbot handler (async, non-blocking)
        try:
            await chatbot.handle_message(parsed_message)
        except Exception as e:
            # Log error but still return 200 to Meta
            logger.error(f"Error processing Instagram message: {str(e)}", exc_info=True)
        
        # Always return 200 OK to Meta within 20 seconds
        return JSONResponse(content={"status": "received"}, status_code=200)
    
    except HTTPException:
        # Signature verification failed - return error
        raise
    except Exception as e:
        logger.error(f"Instagram webhook error: {str(e)}", exc_info=True)
        # Return 200 to prevent Meta retries
        return JSONResponse(content={"status": "error"}, status_code=200)


@router.get("/health")
async def webhook_health():
    """
    Health check endpoint for webhook integration.
    
    Returns:
        200 OK with status information
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "TrustGuard Meta Webhooks",
        "endpoints": {
            "whatsapp": "/integrations/webhook/whatsapp",
            "instagram": "/integrations/webhook/instagram"
        }
    })
