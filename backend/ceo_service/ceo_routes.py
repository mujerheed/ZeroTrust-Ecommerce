"""
FastAPI routes for CEO admin operations.

This module provides endpoints for:
- CEO registration and authentication
- Vendor onboarding and management
- Order approval workflows (flagged + high-value)
- Dashboard metrics and reporting
- Audit log access
- Multi-CEO tenancy enforcement
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from .ceo_logic import (
    register_ceo, authenticate_ceo,
    onboard_vendor, list_vendors_for_ceo, remove_vendor_by_ceo,
    get_dashboard_metrics,
    get_pending_approvals, approve_order, reject_order, request_approval_otp,
    get_audit_logs_for_ceo,
    update_ceo_profile
)
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
    password: str
    company_name: Optional[str] = None


class CEOLoginRequest(BaseModel):
    email: EmailStr
    password: str


class VendorOnboardRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: Optional[str] = None


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


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_ceo_endpoint(req: CEORegisterRequest):
    try:
        ceo = register_ceo(
            name=req.name,
            email=req.email,
            phone=req.phone,
            password=req.password,
            company_name=req.company_name
        )
        
        logger.info("CEO registered via API", extra={"ceo_id": ceo.get("ceo_id"), "email": req.email})
        
        return format_response("success", "CEO account created successfully", {"ceo": ceo})
    
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
    try:
        result = authenticate_ceo(email=req.email, password=req.password)
        
        logger.info("CEO logged in via API", extra={"ceo_id": result["ceo"].get("ceo_id"), "email": req.email})
        
        return format_response("success", "Authentication successful", result)
    
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
    try:
        result = onboard_vendor(
            ceo_id=ceo_id,
            name=req.name,
            email=req.email,
            phone=req.phone,
            password=req.password
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
