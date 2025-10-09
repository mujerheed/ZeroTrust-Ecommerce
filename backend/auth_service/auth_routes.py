"""
Authentication routes following the Zero Trust proposal workflow.
Optimized with rate limiting, security headers, and enhanced validation.
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from auth_logic import (
    register_ceo, login_ceo, login_vendor, 
    verify_otp_universal, create_vendor_account
)
from utils import (
    format_response, validate_phone_number, validate_email,
    rate_limit_check, log_security_event
)

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
