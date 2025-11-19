"""
FastAPI routes for CEO admin operations.

This module provides endpoints for:
- CEO registration and authentication
- Vendor onboarding and management
- Order approval workflows (flagged + high-value)
- Dashboard metrics and reporting
- Audit log access
- Multi-CEO tenancy enforcement
- OAuth Meta Connection (WhatsApp/Instagram)
"""

import os
import time
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from .ceo_logic import (
    register_ceo, authenticate_ceo,
    onboard_vendor, list_vendors_for_ceo, remove_vendor_by_ceo,
    get_dashboard_metrics,
    get_pending_approvals, approve_order, reject_order, request_approval_otp,
    get_audit_logs_for_ceo,
    update_ceo_profile,
    get_chatbot_settings,
    update_chatbot_settings,
    preview_chatbot_conversation
)
from common.analytics import get_ceo_fraud_trends, get_vendor_performance_summary
from .utils import format_response, verify_ceo_token
from common.logger import logger

router = APIRouter()
security = HTTPBearer()


def get_current_ceo(token=Depends(security)) -> str:
    ceo_id = verify_ceo_token(token.credentials)
    if not ceo_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return ceo_id


class CEORegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company_name: Optional[str] = None


class CEOLoginRequest(BaseModel):
    contact: str  # Phone or email for OTP delivery


class VendorOnboardRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str


class OrderApprovalRequest(BaseModel):
    otp: Optional[str] = None
    notes: Optional[str] = None


class OrderRejectionRequest(BaseModel):
    reason: str


class CEOProfileUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    phone: Optional[str] = None
    business_hours: Optional[str] = None
    delivery_fee: Optional[float] = None
    email: Optional[EmailStr] = None
    otp: Optional[str] = None  # Required if updating email


class ChatbotSettingsUpdateRequest(BaseModel):
    welcome_message: Optional[str] = None
    business_hours: Optional[str] = None
    tone: Optional[str] = None  # friendly, professional, casual
    language: Optional[str] = None  # ISO 639-1 code (e.g., "en", "fr")
    auto_responses: Optional[Dict[str, str]] = None
    enabled_features: Optional[Dict[str, bool]] = None


class ChatbotPreviewRequest(BaseModel):
    user_message: str
    settings: Optional[Dict[str, Any]] = None  # Optional custom settings to preview


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_ceo_endpoint(req: CEORegisterRequest):
    """
    CEO registration with OTP verification (Zero Trust).
    Sends 6-character OTP via SMS/Email.
    """
    try:
        ceo = register_ceo(
            name=req.name,
            email=req.email,
            phone=req.phone,
            company_name=req.company_name
        )
        
        logger.info("CEO registered via API", extra={"ceo_id": ceo.get("ceo_id"), "email": req.email})
        
        return format_response("success", "CEO registration initiated. Check SMS/Email for 6-digit OTP to complete setup.", {
            "ceo": ceo,
            "otp_format": "6-digit numbers + symbols",
            "ttl_minutes": 5
        })
    
    except ValueError as e:
        error_message = str(e)
        if "already registered" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("CEO registration failed", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


@router.post("/login")
async def login_ceo_endpoint(req: CEOLoginRequest):
    """
    CEO login with OTP verification (Zero Trust).
    Sends 6-character OTP via SMS/Email.
    """
    try:
        from auth_service.auth_logic import login_ceo
        
        result = login_ceo(req.contact)
        
        logger.info("CEO login OTP sent", extra={"contact": req.contact})
        
        return format_response("success", "CEO OTP sent. Check SMS/Email for 6-digit code.", {
            "otp_format": "6-digit numbers + symbols",
            "ttl_minutes": 5,
            "next_step": "POST /auth/verify-otp with the OTP code"
        })
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("CEO login failed", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.patch("/profile")
async def update_profile_endpoint(req: CEOProfileUpdateRequest, ceo_id: str = Depends(get_current_ceo)):
    """
    Update CEO profile information.
    
    Regular fields (company_name, phone, business_hours, delivery_fee) can be updated directly.
    Sensitive fields (email) require OTP verification.
    
    Request:
        {
            "company_name": "Alice's Electronics Ltd.",
            "phone": "+2348012345678",
            "business_hours": "Mon-Fri 9AM-6PM, Sat 10AM-4PM",
            "delivery_fee": 2500.00,
            "email": "newemail@example.com",  // Optional, requires OTP
            "otp": "123456"  // Required if updating email
        }
    
    Response:
        {
            "status": "success",
            "message": "Profile updated successfully",
            "data": {
                "ceo_id": "ceo_...",
                "company_name": "Alice's Electronics Ltd.",
                ...
            }
        }
    """
    try:
        updated_ceo = update_ceo_profile(
            ceo_id=ceo_id,
            company_name=req.company_name,
            phone=req.phone,
            business_hours=req.business_hours,
            delivery_fee=req.delivery_fee,
            email=req.email,
            otp=req.otp
        )
        
        logger.info("CEO profile updated via API", extra={"ceo_id": ceo_id})
        
        return format_response("success", "Profile updated successfully", {"ceo": updated_ceo})
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "otp" in error_message.lower() and "required" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        elif "invalid" in error_message.lower() or "expired" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)
        elif "already in use" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("CEO profile update failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")


@router.post("/vendors", status_code=status.HTTP_201_CREATED)
async def onboard_vendor_endpoint(req: VendorOnboardRequest, ceo_id: str = Depends(get_current_ceo)):
    """
    CEO onboards a vendor. Vendor will receive OTP for first login.
    """
    try:
        result = onboard_vendor(
            ceo_id=ceo_id,
            name=req.name,
            email=req.email,
            phone=req.phone
        )
        
        logger.info("Vendor onboarded via API", extra={"ceo_id": ceo_id, "vendor_id": result["vendor"].get("vendor_id")})
        
        return format_response("success", "Vendor onboarded successfully", result)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Vendor onboarding failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Vendor onboarding failed")


@router.get("/vendors")
async def list_vendors_endpoint(ceo_id: str = Depends(get_current_ceo)):
    try:
        vendors = list_vendors_for_ceo(ceo_id)
        
        return format_response("success", f"Retrieved {len(vendors)} vendors", {"vendors": vendors, "count": len(vendors)})
    
    except Exception as e:
        logger.error("List vendors failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vendors")


@router.delete("/vendors/{vendor_id}")
async def delete_vendor_endpoint(vendor_id: str, ceo_id: str = Depends(get_current_ceo)):
    try:
        remove_vendor_by_ceo(ceo_id, vendor_id)
        
        logger.info("Vendor deleted via API", extra={"ceo_id": ceo_id, "vendor_id": vendor_id})
        
        return format_response("success", "Vendor removed successfully", {"vendor_id": vendor_id})
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "unauthorized" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("Delete vendor failed", extra={"ceo_id": ceo_id, "vendor_id": vendor_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete vendor")


@router.get("/dashboard")
async def get_dashboard_endpoint(ceo_id: str = Depends(get_current_ceo)):
    try:
        metrics = get_dashboard_metrics(ceo_id)
        
        return format_response("success", "Dashboard metrics retrieved", {"dashboard": metrics})
    
    except Exception as e:
        logger.error("Get dashboard failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve dashboard metrics")


@router.get("/approvals")
async def get_approvals_endpoint(ceo_id: str = Depends(get_current_ceo)):
    try:
        approvals = get_pending_approvals(ceo_id)
        
        return format_response("success", f"Retrieved {approvals['total_pending']} pending approvals", approvals)
    
    except Exception as e:
        logger.error("Get approvals failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve pending approvals")


@router.post("/approvals/request-otp")
async def request_otp_endpoint(order_id: str = Query(..., description="Order ID requiring approval"), ceo_id: str = Depends(get_current_ceo)):
    try:
        otp = request_approval_otp(ceo_id, order_id)
        
        logger.info("Approval OTP requested via API", extra={"ceo_id": ceo_id, "order_id": order_id})
        
        return format_response("success", "OTP generated for order approval", {"order_id": order_id, "otp_sent": True, "dev_otp": otp})
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "unauthorized" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("Request OTP failed", extra={"ceo_id": ceo_id, "order_id": order_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate OTP")


@router.patch("/approvals/{order_id}/approve")
async def approve_order_endpoint(order_id: str, req: OrderApprovalRequest, ceo_id: str = Depends(get_current_ceo)):
    try:
        updated_order = approve_order(ceo_id=ceo_id, order_id=order_id, otp=req.otp, notes=req.notes)
        
        logger.info("Order approved via API", extra={"ceo_id": ceo_id, "order_id": order_id})
        
        return format_response("success", "Order approved successfully", {"order": updated_order})
    
    except ValueError as e:
        error_message = str(e)
        if "otp" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)
        elif "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "unauthorized" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("Approve order failed", extra={"ceo_id": ceo_id, "order_id": order_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve order")


@router.patch("/approvals/{order_id}/reject")
async def reject_order_endpoint(order_id: str, req: OrderRejectionRequest, ceo_id: str = Depends(get_current_ceo)):
    try:
        updated_order = reject_order(ceo_id=ceo_id, order_id=order_id, reason=req.reason)
        
        logger.info("Order rejected via API", extra={"ceo_id": ceo_id, "order_id": order_id, "reason": req.reason})
        
        return format_response("success", "Order rejected successfully", {"order": updated_order})
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "unauthorized" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("Reject order failed", extra={"ceo_id": ceo_id, "order_id": order_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject order")


@router.get("/audit-logs")
async def get_audit_logs_endpoint(limit: int = Query(100, description="Maximum number of logs to return"), ceo_id: str = Depends(get_current_ceo)):
    try:
        logs = get_audit_logs_for_ceo(ceo_id, limit)
        
        return format_response("success", f"Retrieved {len(logs)} audit log entries", {"logs": logs, "count": len(logs)})
    
    except Exception as e:
        logger.error("Get audit logs failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve audit logs")


# ==================== OAuth Meta Connection Routes ====================

from fastapi.responses import RedirectResponse
from .oauth_meta import (
    get_authorization_url,
    handle_oauth_callback,
    get_connection_status,
    revoke_connection
)


class OAuthCallbackResponse(BaseModel):
    code: str
    state: str


@router.get("/oauth/meta/authorize")
async def oauth_authorize_endpoint(
    platform: str = Query(..., description="Platform to connect: 'whatsapp' or 'instagram'"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Initiate Meta OAuth flow.
    
    Redirects CEO to Meta's OAuth consent screen for WhatsApp or Instagram.
    
    **Query Parameters:**
    - `platform`: 'whatsapp' or 'instagram'
    
    **Returns:**
    - Redirect to Meta OAuth authorization URL
    
    **Example:**
    ```
    GET /ceo/oauth/meta/authorize?platform=whatsapp
    Authorization: Bearer <JWT_TOKEN>
    ```
    """
    try:
        # Build redirect URI (your application's callback URL)
        from fastapi import Request
        # In production, use configured callback URL from environment
        redirect_uri = f"{os.getenv('OAUTH_CALLBACK_BASE_URL', 'http://localhost:8000')}/ceo/oauth/meta/callback"
        
        # Generate authorization URL
        auth_url = get_authorization_url(ceo_id, platform, redirect_uri)
        
        logger.info("OAuth authorization initiated", extra={
            "ceo_id": ceo_id,
            "platform": platform
        })
        
        # Redirect to Meta OAuth consent screen
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("OAuth authorization failed", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate OAuth")


@router.get("/oauth/meta/callback")
async def oauth_callback_endpoint(
    code: str = Query(..., description="Authorization code from Meta"),
    state: str = Query(..., description="State token for CSRF protection")
):
    """
    Handle OAuth callback from Meta.
    
    Meta redirects here after user grants/denies permission.
    Exchanges authorization code for access token and stores in Secrets Manager.
    
    **Query Parameters:**
    - `code`: Authorization code from Meta
    - `state`: State token (CSRF protection)
    
    **Returns:**
    - Connection status with expiry info
    
    **Example:**
    ```
    GET /ceo/oauth/meta/callback?code=ABC123&state=XYZ789
    ```
    
    **Note:** This endpoint is called by Meta, not directly by the frontend.
    """
    try:
        # Build redirect URI (must match authorization request)
        redirect_uri = f"{os.getenv('OAUTH_CALLBACK_BASE_URL', 'http://localhost:8000')}/ceo/oauth/meta/callback"
        
        # Handle callback (validates state, exchanges code for token, stores token)
        connection_data = handle_oauth_callback(code, state, redirect_uri)
        
        logger.info("OAuth callback handled successfully", extra={
            "ceo_id": connection_data["ceo_id"],
            "platform": connection_data["platform"]
        })
        
        # Redirect to frontend success page
        frontend_redirect = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/ceo/oauth/success?platform={connection_data['platform']}"
        
        return RedirectResponse(url=frontend_redirect, status_code=status.HTTP_302_FOUND)
    
    except ValueError as e:
        # Redirect to frontend error page
        frontend_error = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/ceo/oauth/error?error={str(e)}"
        return RedirectResponse(url=frontend_error, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        logger.error("OAuth callback failed", extra={"error": str(e)})
        frontend_error = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/ceo/oauth/error?error=callback_failed"
        return RedirectResponse(url=frontend_error, status_code=status.HTTP_302_FOUND)


@router.get("/oauth/meta/status")
async def oauth_status_endpoint(
    platform: str = Query(..., description="Platform to check: 'whatsapp' or 'instagram'"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Check Meta OAuth connection status.
    
    Returns connection status, expiry info, and whether token needs refresh.
    
    **Query Parameters:**
    - `platform`: 'whatsapp' or 'instagram'
    
    **Returns:**
    - Connection status with:
      - `connected`: boolean
      - `connected_at`: timestamp
      - `expires_at`: timestamp
      - `days_until_expiry`: number
      - `needs_refresh`: boolean (true if < 7 days until expiry)
    
    **Example:**
    ```
    GET /ceo/oauth/meta/status?platform=whatsapp
    Authorization: Bearer <JWT_TOKEN>
    
    Response:
    {
      "status": "success",
      "message": "Connection status retrieved",
      "data": {
        "platform": "whatsapp",
        "connected": true,
        "connected_at": 1700400000,
        "expires_at": 1705584000,
        "days_until_expiry": 45,
        "needs_refresh": false
      }
    }
    ```
    """
    try:
        status_data = get_connection_status(ceo_id, platform)
        
        return format_response("success", "Connection status retrieved", status_data)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Get OAuth status failed", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get connection status")


@router.post("/oauth/meta/revoke")
async def oauth_revoke_endpoint(
    platform: str = Query(..., description="Platform to disconnect: 'whatsapp' or 'instagram'"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Revoke Meta OAuth connection.
    
    Deletes access token from Secrets Manager and updates CEO record.
    
    **Query Parameters:**
    - `platform`: 'whatsapp' or 'instagram'
    
    **Returns:**
    - Disconnection confirmation
    
    **Example:**
    ```
    POST /ceo/oauth/meta/revoke?platform=whatsapp
    Authorization: Bearer <JWT_TOKEN>
    
    Response:
    {
      "status": "success",
      "message": "WhatsApp connection revoked",
      "data": {
        "platform": "whatsapp",
        "connected": false,
        "disconnected_at": 1700400000
      }
    }
    ```
    """
    try:
        revoke_connection(ceo_id, platform)
        
        logger.info("OAuth connection revoked via API", extra={
            "ceo_id": ceo_id,
            "platform": platform
        })
        
        return format_response(
            "success",
            f"{platform.capitalize()} connection revoked",
            {
                "platform": platform,
                "connected": False,
                "disconnected_at": int(time.time())
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Revoke OAuth connection failed", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke connection")


# ==================== Chatbot Customization Endpoints ====================

@router.get("/chatbot-settings")
async def get_chatbot_settings_endpoint(ceo_id: str = Depends(get_current_ceo)):
    """
    Get chatbot customization settings.
    
    Returns current chatbot settings for the CEO including:
    - Welcome message
    - Business hours
    - Tone (friendly, professional, casual)
    - Language
    - Auto-responses
    - Enabled features
    
    Example:
    ```
    GET /ceo/chatbot-settings
    Authorization: Bearer <JWT_TOKEN>
    
    Response:
    {
      "status": "success",
      "message": "Chatbot settings retrieved",
      "data": {
        "welcome_message": "Welcome! How can I help you?",
        "business_hours": "Mon-Fri 9AM-6PM",
        "tone": "friendly",
        "language": "en",
        "auto_responses": {
          "greeting": "Hello! Welcome to our store.",
          "thanks": "You're welcome!",
          "goodbye": "Have a great day!"
        },
        "enabled_features": {
          "address_collection": true,
          "order_tracking": true,
          "receipt_upload": true
        }
      }
    }
    ```
    """
    try:
        settings = get_chatbot_settings(ceo_id)
        
        logger.info("Chatbot settings retrieved via API", extra={"ceo_id": ceo_id})
        
        return format_response(
            "success",
            "Chatbot settings retrieved",
            settings
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Get chatbot settings failed", extra={
            "ceo_id": ceo_id,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve settings")


@router.patch("/chatbot-settings")
async def update_chatbot_settings_endpoint(
    req: ChatbotSettingsUpdateRequest,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Update chatbot customization settings.
    
    Updates chatbot behavior and appearance:
    - welcome_message: Custom greeting message (max 500 chars)
    - business_hours: Operating hours text
    - tone: Chatbot personality (friendly/professional/casual)
    - language: ISO 639-1 language code
    - auto_responses: Custom responses for common intents
    - enabled_features: Toggle chatbot features on/off
    
    Example:
    ```
    PATCH /ceo/chatbot-settings
    Authorization: Bearer <JWT_TOKEN>
    Content-Type: application/json
    
    {
      "welcome_message": "👋 Welcome to Alice's Store! How may I assist you today?",
      "tone": "professional",
      "auto_responses": {
        "greeting": "Good day! Welcome to our store.",
        "thanks": "You are most welcome."
      }
    }
    
    Response:
    {
      "status": "success",
      "message": "Chatbot settings updated",
      "data": {
        "welcome_message": "👋 Welcome to Alice's Store!...",
        "tone": "professional",
        "updated_at": 1700400000
      }
    }
    ```
    """
    try:
        updated_settings = update_chatbot_settings(
            ceo_id=ceo_id,
            welcome_message=req.welcome_message,
            business_hours=req.business_hours,
            tone=req.tone,
            language=req.language,
            auto_responses=req.auto_responses,
            enabled_features=req.enabled_features
        )
        
        logger.info("Chatbot settings updated via API", extra={"ceo_id": ceo_id})
        
        return format_response(
            "success",
            "Chatbot settings updated",
            {
                **updated_settings,
                "updated_at": int(time.time())
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Update chatbot settings failed", extra={
            "ceo_id": ceo_id,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update settings")


@router.post("/chatbot/preview")
async def preview_chatbot_endpoint(
    req: ChatbotPreviewRequest,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Preview chatbot response with custom settings.
    
    Simulates a chatbot conversation to preview how the bot
    will respond with current or custom settings.
    
    Use this to test chatbot behavior before saving changes.
    
    Example:
    ```
    POST /ceo/chatbot/preview
    Authorization: Bearer <JWT_TOKEN>
    Content-Type: application/json
    
    {
      "user_message": "Hello!",
      "settings": {
        "tone": "professional",
        "auto_responses": {
          "greeting": "Good day, how may I assist you?"
        }
      }
    }
    
    Response:
    {
      "status": "success",
      "message": "Chatbot response preview",
      "data": {
        "user_message": "Hello!",
        "bot_response": "Good day, how may I assist you?",
        "intent": "greeting",
        "settings_preview": {
          "tone": "professional",
          "language": "en"
        }
      }
    }
    ```
    """
    try:
        preview = preview_chatbot_conversation(
            ceo_id=ceo_id,
            user_message=req.user_message,
            settings=req.settings
        )
        
        logger.info("Chatbot preview generated via API", extra={
            "ceo_id": ceo_id,
            "intent": preview.get("intent")
        })
        
        return format_response(
            "success",
            "Chatbot response preview",
            preview
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Chatbot preview failed", extra={
            "ceo_id": ceo_id,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate preview")


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/fraud-trends", status_code=status.HTTP_200_OK)
async def get_fraud_trends(
    days: int = Query(default=7, ge=1, le=90),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get daily fraud flag counts over the past N days for charts.
    
    Query params:
        - days: Number of days to look back (1-90, default 7)
    
    Returns:
        Array of {date: "YYYY-MM-DD", fraud_count: number}
    """
    try:
        trend_data = get_ceo_fraud_trends(ceo_id, days)
        
        return format_response(
            "success",
            f"Fraud trend data for past {days} days",
            {
                "data": trend_data,
                "days_requested": days,
                "total_fraud_events": sum(d["fraud_count"] for d in trend_data)
            }
        )
    except Exception as e:
        logger.error("Failed to retrieve fraud trends", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve fraud trends")


@router.get("/analytics/vendor-performance", status_code=status.HTTP_200_OK)
async def get_vendor_performance(
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get performance summary for all vendors (for table/chart display).
    
    Returns:
        Array of vendor performance metrics:
        [
            {
                "vendor_id": "vendor_123",
                "vendor_name": "Ada's Fashion",
                "total_orders": 42,
                "flag_rate": 0.024,  # 2.4%
                "avg_approval_time_minutes": 18
            },
            ...
        ]
    """
    try:
        performance_data = get_vendor_performance_summary(ceo_id)
        
        return format_response(
            "success",
            f"Vendor performance data for {len(performance_data)} vendors",
            {
                "vendors": performance_data,
                "total_vendors": len(performance_data)
            }
        )
    except Exception as e:
        logger.error("Failed to retrieve vendor performance", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vendor performance")
