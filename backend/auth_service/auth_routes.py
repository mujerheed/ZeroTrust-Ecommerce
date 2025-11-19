"""
Authentication routes following the Zero Trust proposal workflow.
Optimized with rate limiting, security headers, and enhanced validation.
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from .auth_logic import (
    register_ceo, login_ceo, login_vendor, 
    verify_otp_universal, create_vendor_account
)
from .utils import (
    format_response, validate_phone_number, validate_email,
    rate_limit_check, log_security_event
)
from ceo_service.utils import verify_ceo_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

# ========== CEO SELF-REGISTRATION (As per proposal) ==========
class CEORegisterRequest(BaseModel):
    name: str
    phone: str  
    email: EmailStr

@router.post("/ceo/register", status_code=status.HTTP_201_CREATED)
async def ceo_register(request: Request, req: CEORegisterRequest):
    """
    CEO self-registration as specified in proposal.
    Sends 6-character digits+symbols OTP for verification.
    """
    try:
        # Rate limiting for registration attempts
        rate_limit_check(request.client.host, "ceo_register", max_attempts=3, window_minutes=60)
        
        # Validation
        validate_phone_number(req.phone)
        validate_email(req.email)
        
        # Create CEO account and send OTP
        ceo_id = register_ceo(req.name, req.phone, req.email)
        
        log_security_event(ceo_id, "CEO_REGISTER_INITIATED", {
            "ip": request.client.host,
            "email": req.email
        })
        
        return format_response("success", "CEO registration initiated. Check SMS/Email for 6-digit OTP.", {
            "ceo_id": ceo_id,
            "otp_format": "6-digit numbers + symbols",
            "ttl_minutes": 5
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========== CEO LOGIN (As per proposal) ==========
class CEOLoginRequest(BaseModel):
    contact: str  # Phone or email

@router.post("/ceo/login")
async def ceo_login(request: Request, req: CEOLoginRequest):
    """
    CEO login with phone/email as per proposal.
    Sends 6-character digits+symbols OTP.
    """
    try:
        rate_limit_check(request.client.host, "ceo_login", max_attempts=5, window_minutes=15)
        
        ceo_id = login_ceo(req.contact)
        
        log_security_event(ceo_id, "CEO_LOGIN_OTP_SENT", {
            "ip": request.client.host,
            "contact_method": "email" if "@" in req.contact else "phone"
        })
        
        return format_response("success", "CEO OTP sent. Check SMS/Email for 6-digit code.", {
            "ceo_id": ceo_id,
            "otp_format": "6-digit numbers + symbols"
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========== VENDOR LOGIN (CEO Pre-registered) ==========
class VendorLoginRequest(BaseModel):
    phone: str

@router.post("/vendor/login")
async def vendor_login(request: Request, req: VendorLoginRequest):
    """
    Vendor login with phone number (CEO must have registered vendor).
    Sends 8-character alphanumeric+special OTP.
    """
    try:
        rate_limit_check(request.client.host, "vendor_login", max_attempts=5, window_minutes=15)
        
        validate_phone_number(req.phone)
        vendor_id = login_vendor(req.phone)
        
        log_security_event(vendor_id, "VENDOR_LOGIN_OTP_SENT", {
            "ip": request.client.host,
            "phone": req.phone[-4:]  # Log last 4 digits only
        })
        
        return format_response("success", "Vendor OTP sent to registered phone.", {
            "vendor_id": vendor_id,
            "otp_format": "8-character alphanumeric + symbols"
        })
        
    except Exception as e:
        raise HTTPException(status_code=404, detail="Vendor not found. Contact CEO for registration.")

# ========== UNIVERSAL OTP VERIFICATION ==========
class VerifyOTPRequest(BaseModel):
    user_id: str
    otp: str

@router.post("/verify-otp")
async def verify_otp(request: Request, req: VerifyOTPRequest):
    """
    Universal OTP verification for CEO and Vendor.
    Buyer OTP verification handled by webhook bot.
    """
    try:
        rate_limit_check(request.client.host, "otp_verify", max_attempts=3, window_minutes=10)
        
        result = verify_otp_universal(req.user_id, req.otp)
        
        log_security_event(req.user_id, "OTP_VERIFIED_SUCCESS", {
            "ip": request.client.host,
            "role": result["role"]
        })
        
        return format_response("success", f"{result['role']} authentication successful.", {
            "token": result["token"],
            "role": result["role"],
            "expires_minutes": 30
        })
        
    except Exception as e:
        log_security_event(req.user_id, "OTP_VERIFICATION_FAILED", {
            "ip": request.client.host,
            "error": str(e)
        })
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

# ========== WEBHOOK FOR BUYER BOT (Optimization) ==========
@router.post("/webhook/buyer-otp")
async def buyer_bot_otp_webhook(request: Request, payload: dict):
    """
    Webhook endpoint for WhatsApp/Instagram bot to verify buyer OTPs.
    Called when buyer submits OTP in chat.
    """
    try:
        # Verify webhook signature for security
        # webhook_signature_verify(request.headers.get("X-Hub-Signature-256"))
        
        buyer_id = payload.get("buyer_id")
        otp = payload.get("otp")
        platform = payload.get("platform")  # "whatsapp" or "instagram"
        
        if not all([buyer_id, otp, platform]):
            raise ValueError("Missing required webhook data")
            
        result = verify_otp_universal(buyer_id, otp)
        
        log_security_event(buyer_id, "BUYER_OTP_VERIFIED", {
            "platform": platform,
            "chat_id": payload.get("chat_id")
        })
        
        return format_response("success", "Buyer verified successfully.", {
            "buyer_id": buyer_id,
            "verified": True,
            "order_can_proceed": True
        })
        
    except Exception as e:
        return format_response("error", f"Buyer OTP verification failed: {str(e)}")

# ========== ADMIN ENDPOINT - CREATE VENDOR (CEO Only) ==========
class CreateVendorRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr

@router.post("/admin/create-vendor")
async def create_vendor(request: Request, req: CreateVendorRequest, token: str = security):
    """
    CEO-only endpoint to create vendor accounts.
    Requires CEO JWT token for authorization.
    """
    try:
        # Verify CEO token
        ceo_id = verify_ceo_token(token.credentials if token else None)
        
        
        validate_phone_number(req.phone)
        validate_email(req.email)
        
        vendor_id = create_vendor_account(req.name, req.phone, req.email, created_by=ceo_id)
        
        log_security_event(ceo_id, "VENDOR_CREATED", {
            "vendor_id": vendor_id,
            "vendor_phone": req.phone[-4:]
        })
        
        return format_response("success", "Vendor account created successfully.", {
            "vendor_id": vendor_id
        })
        
    except Exception as e:
        raise HTTPException(status_code=403, detail="Unauthorized or invalid request")


# ========== BUYER AUTHENTICATION VIA WEBHOOKS ==========

@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    WhatsApp webhook verification endpoint (GET).
    
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    when setting up the webhook in Business Manager.
    
    Query Params:
        hub.mode: 'subscribe'
        hub.verify_token: Verification token (must match env config)
        hub.challenge: Random string to echo back
    
    Returns:
        challenge value if verification successful
    """
    from integrations.webhook_handler import handle_webhook_challenge
    
    try:
        result = await handle_webhook_challenge(request)
        return result['challenge']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/whatsapp")
async def whatsapp_webhook_receive(request: Request):
    """
    WhatsApp webhook message receiver (POST).
    
    Receives incoming messages from WhatsApp Business API.
    Validates HMAC signature and routes to chatbot.
    
    Headers:
        X-Hub-Signature-256: HMAC-SHA256 signature
    
    Body:
        WhatsApp webhook payload (JSON)
    
    Returns:
        200 OK to acknowledge receipt
    """
    from integrations.webhook_handler import (
        verify_meta_signature,
        parse_whatsapp_message,
        extract_ceo_id_from_metadata,
        process_webhook_message
    )
    from common.config import settings
    
    try:
        # Get app secret from environment or Secrets Manager
        app_secret = getattr(settings, 'META_APP_SECRET', 'dev_secret')
        
        # Verify HMAC signature
        await verify_meta_signature(request, app_secret)
        
        # Parse request body
        body = await request.json()
        
        # Parse WhatsApp message
        parsed_message = parse_whatsapp_message(body)
        
        if not parsed_message:
            # Not a message event (could be status update)
            return {"status": "ignored"}
        
        # Extract CEO ID for multi-tenancy
        ceo_id = extract_ceo_id_from_metadata(parsed_message)
        
        # Process message and route to chatbot
        result = await process_webhook_message(parsed_message, ceo_id)
        
        return {"status": "processed", "action": result.get('action')}
    
    except HTTPException:
        raise
    except Exception as e:
        # Log error but return 200 to prevent Meta from retrying
        from common.logger import logger
        logger.error(f"WhatsApp webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/webhook/instagram")
async def instagram_webhook_verify(request: Request):
    """
    Instagram webhook verification endpoint (GET).
    
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    when setting up the webhook in Business Manager.
    
    Query Params:
        hub.mode: 'subscribe'
        hub.verify_token: Verification token (must match env config)
        hub.challenge: Random string to echo back
    
    Returns:
        challenge value if verification successful
    """
    from integrations.webhook_handler import handle_webhook_challenge
    
    try:
        result = await handle_webhook_challenge(request)
        return result['challenge']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/instagram")
async def instagram_webhook_receive(request: Request):
    """
    Instagram webhook message receiver (POST).
    
    Receives incoming messages from Instagram Messaging API.
    Validates HMAC signature and routes to chatbot.
    
    Headers:
        X-Hub-Signature-256: HMAC-SHA256 signature
    
    Body:
        Instagram webhook payload (JSON)
    
    Returns:
        200 OK to acknowledge receipt
    """
    from integrations.webhook_handler import (
        verify_meta_signature,
        parse_instagram_message,
        extract_ceo_id_from_metadata,
        process_webhook_message
    )
    from common.config import settings
    
    try:
        # Get app secret from environment or Secrets Manager
        app_secret = getattr(settings, 'META_APP_SECRET', 'dev_secret')
        
        # Verify HMAC signature
        await verify_meta_signature(request, app_secret)
        
        # Parse request body
        body = await request.json()
        
        # Parse Instagram message
        parsed_message = parse_instagram_message(body)
        
        if not parsed_message:
            # Not a message event
            return {"status": "ignored"}
        
        # Extract CEO ID for multi-tenancy
        ceo_id = extract_ceo_id_from_metadata(parsed_message)
        
        # Process message and route to chatbot
        result = await process_webhook_message(parsed_message, ceo_id)
        
        return {"status": "processed", "action": result.get('action')}
    
    except HTTPException:
        raise
    except Exception as e:
        # Log error but return 200 to prevent Meta from retrying
        from common.logger import logger
        logger.error(f"Instagram webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

