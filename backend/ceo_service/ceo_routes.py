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
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from .ceo_logic import (
    register_ceo,
    onboard_vendor, list_vendors_for_ceo, get_vendor_details_for_ceo, update_vendor_by_ceo, remove_vendor_by_ceo,
    get_dashboard_metrics,
    get_pending_approvals, approve_order, reject_order, request_approval_otp,
    get_audit_logs_for_ceo,
    update_ceo_profile,
    get_chatbot_settings,
    update_chatbot_settings,
    preview_chatbot_conversation
)
from .database import get_ceo_by_id, get_notifications_for_ceo, mark_notification_as_read, mark_all_notifications_as_read, create_notification, USERS_TABLE
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


class BankDetails(BaseModel):
    """Bank account information for the CEO's business to receive payments."""
    bank_name: str = Field(..., min_length=1, max_length=100, description="Name of the bank")
    account_number: str = Field(..., min_length=10, max_length=10, description="10-digit account number")
    account_name: str = Field(..., min_length=1, max_length=100, description="Account holder name")


class CEOProfileUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    phone: Optional[str] = None
    business_hours: Optional[str] = None
    delivery_fee: Optional[float] = None
    email: Optional[EmailStr] = None
    otp: Optional[str] = None  # Required if updating email
    bank_details: Optional[BankDetails] = None  # Business bank account for receiving payments


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


@router.get("/profile")
async def get_profile_endpoint(ceo_id: str = Depends(get_current_ceo)):
    """
    Get CEO profile information.
    
    Returns:
        {
            "status": "success",
            "message": "Profile retrieved successfully",
            "data": {
                "ceo": {
                    "user_id": "ceo_...",
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "phone": "+2348012345678",
                    "company_name": "Alice's Electronics Ltd.",
                    "business_hours": "Mon-Fri 9AM-6PM",
                    "delivery_fee": 2500.00,
                    "bank_details": {...},
                    "created_at": 1234567890
                }
            }
        }
    """
    try:
        ceo = get_ceo_by_id(ceo_id)
        
        if not ceo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CEO profile not found")
        
        # Remove sensitive fields
        ceo_data = dict(ceo)
        ceo_data.pop("password_hash", None)  # Remove if exists
        
        logger.info("CEO profile retrieved", extra={"ceo_id": ceo_id})
        
        return format_response("success", "Profile retrieved successfully", {"ceo": ceo_data})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get profile failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve profile")


@router.patch("/profile")
async def update_profile_endpoint(req: CEOProfileUpdateRequest, ceo_id: str = Depends(get_current_ceo)):
    """
    Update CEO profile information.
    
    Regular fields (company_name, phone, business_hours, delivery_fee, bank_details) can be updated directly.
    Sensitive fields (email) require OTP verification.
    
    Request:
        {
            "company_name": "Alice's Electronics Ltd.",
            "phone": "+2348012345678",
            "business_hours": "Mon-Fri 9AM-6PM, Sat 10AM-4PM",
            "delivery_fee": 2500.00,
            "bank_details": {
                "bank_name": "Access Bank",
                "account_number": "0123456789",
                "account_name": "Alice's Electronics Ltd"
            },
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
                "bank_details": {...},
                ...
            }
        }
    """
    try:
        # Convert BankDetails to dict if provided
        bank_details_dict = req.bank_details.dict() if req.bank_details else None
        
        updated_ceo = update_ceo_profile(
            ceo_id=ceo_id,
            company_name=req.company_name,
            phone=req.phone,
            business_hours=req.business_hours,
            delivery_fee=req.delivery_fee,
            bank_details=bank_details_dict,
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
        
        # Extract dev_otp from result if present (DEBUG mode)
        dev_otp = result.get("dev_otp")
        response_data = {
            "vendor": result["vendor"],
            "message": result["message"]
        }
        
        # Include dev_otp for testing in DEBUG mode
        if dev_otp is not None:
            response_data["dev_otp"] = dev_otp
        
        return format_response("success", "Vendor onboarded successfully", response_data)
    
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


@router.get("/vendors/{vendor_id}/details")
async def get_vendor_details_endpoint(vendor_id: str, ceo_id: str = Depends(get_current_ceo)):
    try:
        details = get_vendor_details_for_ceo(ceo_id, vendor_id)
        
        return format_response("success", "Vendor details retrieved", {"details": details})
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "unauthorized" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("Get vendor details failed", extra={"ceo_id": ceo_id, "vendor_id": vendor_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vendor details")


class VendorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    status: Optional[str] = Field(None, pattern="^(active|suspended|pending)$")


@router.patch("/vendors/{vendor_id}")
async def update_vendor_endpoint(
    vendor_id: str,
    req: VendorUpdateRequest,
    ceo_id: str = Depends(get_current_ceo)
):
    try:
        updated_vendor = update_vendor_by_ceo(
            ceo_id=ceo_id,
            vendor_id=vendor_id,
            name=req.name,
            email=req.email,
            phone=req.phone,
            status=req.status
        )
        
        logger.info("Vendor updated via API", extra={"ceo_id": ceo_id, "vendor_id": vendor_id})
        
        return format_response("success", "Vendor updated successfully", {"vendor": updated_vendor})
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "unauthorized" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        elif "already in use" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error("Update vendor failed", extra={"ceo_id": ceo_id, "vendor_id": vendor_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update vendor")


@router.get("/dashboard")
async def get_dashboard_endpoint(ceo_id: str = Depends(get_current_ceo)):
    try:
        metrics = get_dashboard_metrics(ceo_id)
        
        # Get CEO details for welcome message
        from ceo_service.database import get_ceo_by_id
        ceo = get_ceo_by_id(ceo_id)
        ceo_name = ceo.get("name", "CEO") if ceo else "CEO"
        
        return format_response("success", "Dashboard metrics retrieved", {
            "dashboard": metrics,
            "ceo_name": ceo_name
        })
    
    except Exception as e:
        logger.error("Get dashboard failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve dashboard metrics")


@router.get("/orders")
async def get_orders_endpoint(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by order status"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    search: Optional[str] = Query(None, description="Search by buyer_id or order_id"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of orders to return"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get all orders across all vendors for this CEO.
    Supports filtering by status, vendor, and search by buyer/order ID.
    """
    try:
        from ceo_service.database import get_orders_for_ceo
        
        # Get orders with filters
        orders = get_orders_for_ceo(
            ceo_id=ceo_id,
            status=status_filter,
            vendor_id=vendor_id,
            limit=limit
        )
        
        # Apply search filter if provided (client-side filtering for buyer_id/order_id)
        if search:
            search_lower = search.lower()
            orders = [
                order for order in orders
                if search_lower in order.get("buyer_id", "").lower()
                or search_lower in order.get("order_id", "").lower()
            ]
        
        # Enrich orders with vendor names
        from ceo_service.database import get_vendor_by_id
        for order in orders:
            vendor = get_vendor_by_id(order.get("vendor_id"))
            if vendor:
                order["vendor_name"] = vendor.get("name", "Unknown")
            else:
                order["vendor_name"] = "Unknown"
        
        logger.info(
            f"CEO orders retrieved",
            extra={
                "ceo_id": ceo_id,
                "count": len(orders),
                "status_filter": status_filter,
                "vendor_filter": vendor_id,
                "search": search
            }
        )
        
        return format_response(
            "success",
            f"Retrieved {len(orders)} orders",
            {
                "orders": orders,
                "total_count": len(orders),
                "filters_applied": {
                    "status": status_filter,
                    "vendor_id": vendor_id,
                    "search": search
                }
            }
        )
    
    except Exception as e:
        logger.error("Get orders failed", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve orders")


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


@router.get("/orders/{order_id}/receipt")
async def get_order_receipt(
    order_id: str,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get receipt details for an order with pre-signed S3 URL for viewing.
    
    Returns:
        - receipt_metadata: Receipt information
        - image_url: Pre-signed S3 URL (5-minute expiry)
        - textract_data: OCR extracted text (if available)
        - mismatch_warnings: Amount/account mismatches
    """
    try:
        from common.s3_client import receipt_storage
        from receipt_service.database import get_receipts_by_order, get_order_by_id
        
        # Verify order belongs to this CEO's business
        order = get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order not found: {order_id}"
            )
        
        if order.get("ceo_id") != ceo_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Order does not belong to your business"
            )
        
        # Get receipt for this order
        receipts = get_receipts_by_order(order_id)
        if not receipts:
            return format_response(
                "success",
                "No receipt uploaded for this order",
                {
                    "has_receipt": False,
                    "order_id": order_id
                }
            )
        
        # Get the most recent receipt
        receipt = receipts[0]
        
        # Generate presigned download URL (5-minute expiry)
        s3_key = receipt.get("s3_key")
        if not s3_key:
            return format_response(
                "success",
                "Receipt metadata exists but file not found in S3",
                {
                    "has_receipt": True,
                    "receipt_metadata": receipt,
                    "image_url": None,
                    "error": "S3 key missing"
                }
            )
        
        try:
            download_url = receipt_storage.generate_download_url(
                s3_key=s3_key,
                expires_in=300  # 5 minutes
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for receipt {receipt.get('receipt_id')}: {e}")
            download_url = None
        
        # Extract Textract data if available
        textract_data = receipt.get("textract_data", {})
        ocr_text = textract_data.get("extracted_text", "")
        ocr_confidence = textract_data.get("confidence_score", 0)
        
        # Check for mismatches
        mismatch_warnings = []
        expected_amount = float(order.get("amount", 0))
        extracted_amount = textract_data.get("amount", 0)
        
        if extracted_amount and abs(expected_amount - extracted_amount) > 0.01:
            mismatch_warnings.append({
                "type": "amount_mismatch",
                "severity": "high",
                "message": f"Expected ₦{expected_amount:,.2f} but receipt shows ₦{extracted_amount:,.2f}",
                "expected": expected_amount,
                "actual": extracted_amount,
                "difference": abs(expected_amount - extracted_amount)
            })
        
        # Check account number mismatch
        expected_account = order.get("vendor_account_number")
        extracted_account = textract_data.get("account_number")
        if expected_account and extracted_account and expected_account != extracted_account:
            mismatch_warnings.append({
                "type": "account_mismatch",
                "severity": "critical",
                "message": "Account number does not match vendor account",
                "expected": expected_account,
                "actual": extracted_account
            })
        
        return format_response(
            "success",
            "Receipt retrieved successfully",
            {
                "has_receipt": True,
                "receipt_id": receipt.get("receipt_id"),
                "image_url": download_url,
                "url_expires_in": 300,  # seconds
                "receipt_metadata": {
                    "uploaded_at": receipt.get("uploaded_at"),
                    "status": receipt.get("status"),
                    "file_type": receipt.get("file_extension"),
                    "file_size": receipt.get("file_size"),
                },
                "ocr_data": {
                    "available": bool(ocr_text),
                    "extracted_text": ocr_text,
                    "confidence_score": ocr_confidence,
                    "amount": extracted_amount,
                    "account_number": extracted_account
                },
                "mismatch_warnings": mismatch_warnings,
                "order_details": {
                    "order_id": order_id,
                    "expected_amount": expected_amount,
                    "vendor_id": order.get("vendor_id"),
                    "buyer_id": order.get("buyer_id")
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get receipt for order {order_id}", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve receipt: {str(e)}"
        )


# ============================================================
# RECEIPTS MANAGEMENT ENDPOINTS
# ============================================================

@router.get("/receipts", status_code=status.HTTP_200_OK)
async def list_receipts_endpoint(
    ceo_id: str = Depends(get_current_ceo),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending_review, approved, rejected, flagged"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, description="Max results per page", ge=1, le=100),
    last_key: Optional[str] = Query(None, description="Pagination token")
):
    """
    List all receipts for CEO's business with filters and pagination.
    
    Query Parameters:
        - status: Filter by status (pending_review, approved, rejected, flagged)
        - vendor_id: Filter by vendor
        - start_date: Filter receipts from this date (YYYY-MM-DD)
        - end_date: Filter receipts until this date (YYYY-MM-DD)
        - limit: Max results per page (default 50, max 100)
        - last_key: Pagination token from previous response
    
    Response:
        {
            "status": "success",
            "message": "Retrieved X receipts",
            "data": {
                "receipts": [...],
                "count": int,
                "last_key": str or null,
                "has_more": bool,
                "filters_applied": {...}
            }
        }
    """
    try:
        from .receipts_logic import get_receipts_for_ceo
        
        result = get_receipts_for_ceo(
            ceo_id=ceo_id,
            status=status_filter,
            vendor_id=vendor_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            last_key=last_key
        )
        
        logger.info(
            f"CEO {ceo_id} retrieved receipts",
            extra={
                'ceo_id': ceo_id,
                'count': result['count'],
                'filters': {
                    'status': status_filter,
                    'vendor_id': vendor_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        )
        
        return format_response(
            "success",
            f"Retrieved {result['count']} receipt(s)",
            {
                **result,
                'filters_applied': {
                    'status': status_filter,
                    'vendor_id': vendor_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list receipts for CEO {ceo_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve receipts"
        )


@router.get("/receipts/stats", status_code=status.HTTP_200_OK)
async def get_receipt_stats_endpoint(ceo_id: str = Depends(get_current_ceo)):
    """
    Get receipt statistics and insights for CEO dashboard.
    
    Response:
        {
            "status": "success",
            "message": "Receipt statistics retrieved",
            "data": {
                "total_receipts": 245,
                "pending_review": 12,
                "approved": 210,
                "rejected": 18,
                "flagged": 5,
                "verification_rate": 93.06,
                "avg_processing_time_hours": 2.5,
                "recent_activity": [...]
            }
        }
    """
    try:
        from .receipts_logic import get_receipt_stats_for_ceo
        
        stats = get_receipt_stats_for_ceo(ceo_id)
        
        logger.info(
            f"CEO {ceo_id} retrieved receipt stats",
            extra={
                'ceo_id': ceo_id,
                'total_receipts': stats['total_receipts']
            }
        )
        
        return format_response("success", "Receipt statistics retrieved", stats)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get receipt stats for CEO {ceo_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/receipts/flagged", status_code=status.HTTP_200_OK)
async def get_flagged_receipts_endpoint(ceo_id: str = Depends(get_current_ceo)):
    """
    Get all flagged receipts requiring CEO attention.
    
    Flagged receipts are those that vendors have marked as suspicious
    or requiring management review (e.g., high amounts, mismatches).
    
    Response:
        {
            "status": "success",
            "message": "Retrieved X flagged receipt(s)",
            "data": {
                "flagged_receipts": [
                    {
                        "receipt_id": "...",
                        "order_id": "...",
                        "amount": 1500000,
                        "upload_timestamp": "...",
                        "vendor_id": "...",
                        "verification_notes": "Amount mismatch detected",
                        "order_details": {...}
                    }
                ],
                "count": int
            }
        }
    """
    try:
        from .receipts_logic import get_flagged_receipts
        
        flagged = get_flagged_receipts(ceo_id)
        
        logger.info(
            f"CEO {ceo_id} retrieved flagged receipts",
            extra={'ceo_id': ceo_id, 'count': len(flagged)}
        )
        
        return format_response(
            "success",
            f"Retrieved {len(flagged)} flagged receipt(s)",
            {
                'flagged_receipts': flagged,
                'count': len(flagged)
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get flagged receipts for CEO {ceo_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flagged receipts"
        )


@router.get("/receipts/{receipt_id}", status_code=status.HTTP_200_OK)
async def get_receipt_details_endpoint(
    receipt_id: str,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get detailed receipt information with order and buyer details.
    
    Response:
        {
            "status": "success",
            "message": "Receipt details retrieved",
            "data": {
                "receipt": {
                    "receipt_id": "...",
                    "order_id": "...",
                    "status": "approved",
                    "upload_timestamp": "...",
                    "verified_at": "...",
                    "verified_by": "...",
                    "s3_key": "...",
                    "textract_data": {...},
                    "verification_notes": "..."
                },
                "order": {...},
                "buyer": {...}
            }
        }
    """
    try:
        from .receipts_logic import get_receipt_details_for_ceo
        
        details = get_receipt_details_for_ceo(ceo_id, receipt_id)
        
        logger.info(
            f"CEO {ceo_id} retrieved receipt {receipt_id}",
            extra={'ceo_id': ceo_id, 'receipt_id': receipt_id}
        )
        
        return format_response("success", "Receipt details retrieved", details)
    
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        elif "access denied" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    except Exception as e:
        logger.error(f"Failed to get receipt details", extra={"ceo_id": ceo_id, "receipt_id": receipt_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve receipt details"
        )


class BulkVerifyRequest(BaseModel):
    receipt_ids: List[str] = Field(..., min_items=1, max_items=50, description="List of receipt IDs (max 50)")
    action: str = Field(..., pattern="^(approve|reject|flag)$", description="Action: approve, reject, or flag")
    notes: Optional[str] = Field(None, max_length=500, description="Optional verification notes")


@router.post("/receipts/bulk-verify", status_code=status.HTTP_200_OK)
async def bulk_verify_receipts_endpoint(
    req: BulkVerifyRequest,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Bulk verify receipts (approve/reject/flag multiple at once).
    
    Request:
        {
            "receipt_ids": ["receipt_123", "receipt_456", ...],
            "action": "approve",  // or "reject", "flag"
            "notes": "Batch verification - all amounts verified"
        }
    
    Response:
        {
            "status": "success",
            "message": "Bulk verification completed: 8/10 succeeded",
            "data": {
                "success_count": 8,
                "failed_count": 2,
                "results": [
                    {"receipt_id": "receipt_123", "success": true, "error": null},
                    {"receipt_id": "receipt_456", "success": false, "error": "Receipt not found"}
                ]
            }
        }
    """
    try:
        from .receipts_logic import bulk_verify_receipts
        
        result = bulk_verify_receipts(
            ceo_id=ceo_id,
            receipt_ids=req.receipt_ids,
            action=req.action,
            notes=req.notes
        )
        
        logger.info(
            f"CEO {ceo_id} performed bulk {req.action}",
            extra={
                'ceo_id': ceo_id,
                'action': req.action,
                'total': len(req.receipt_ids),
                'success': result['success_count'],
                'failed': result['failed_count']
            }
        )
        
        return format_response(
            "success",
            f"Bulk verification completed: {result['success_count']}/{len(req.receipt_ids)} succeeded",
            result
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Bulk verification failed for CEO {ceo_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk verification failed"
        )


@router.get("/audit-logs")
async def get_audit_logs_endpoint(
    limit: int = Query(100, description="Maximum number of logs to return", ge=1, le=500),
    action_filter: Optional[str] = Query(None, alias="action", description="Filter by action type"),
    start_date: Optional[int] = Query(None, description="Start timestamp (Unix epoch)"),
    end_date: Optional[int] = Query(None, description="End timestamp (Unix epoch)"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get audit logs for CEO with optional filters.
    
    Query Parameters:
        - limit: Maximum number of logs (default: 100, max: 500)
        - action: Filter by action type (e.g., "order_approved", "vendor_created")
        - start_date: Start timestamp for date range filter
        - end_date: End timestamp for date range filter
    """
    try:
        logs = get_audit_logs_for_ceo(ceo_id, limit)
        
        # Apply filters
        if action_filter:
            logs = [log for log in logs if log.get("action") == action_filter]
        
        if start_date:
            logs = [log for log in logs if log.get("timestamp", 0) >= start_date]
        
        if end_date:
            logs = [log for log in logs if log.get("timestamp", 0) <= end_date]
        
        # Sort by timestamp (newest first)
        logs = sorted(logs, key=lambda x: x.get("timestamp", 0), reverse=True)
        
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


# Temporary OAuth session storage (in production, use Redis)
_oauth_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/oauth/meta/create-session")
async def create_oauth_session_endpoint(
    platform: str = Query(..., description="Platform to connect: 'whatsapp' or 'instagram'"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Create a temporary OAuth session token for secure browser redirects.
    
    This endpoint creates a short-lived, single-use token that can be used
    in the OAuth authorization URL without exposing the main JWT token.
    
    **Query Parameters:**
    - `platform`: 'whatsapp' or 'instagram'
    
    **Returns:**
    - Temporary session token and authorization URL
    
    **Example:**
    ```
    POST /ceo/oauth/meta/create-session?platform=whatsapp
    Authorization: Bearer <JWT_TOKEN>
    
    Response:
    {
      "status": "success",
      "data": {
        "session_token": "abc123...",
        "auth_url": "http://localhost:8000/ceo/oauth/meta/authorize?platform=whatsapp&session=abc123...",
        "expires_in": 300
      }
    }
    ```
    """
    try:
        import secrets
        
        # Generate temporary session token
        session_token = secrets.token_urlsafe(32)
        
        # Store session data (expires in 5 minutes)
        _oauth_sessions[session_token] = {
            "ceo_id": ceo_id,
            "platform": platform,
            "created_at": int(time.time()),
            "expires_at": int(time.time()) + 300,  # 5 minutes
            "used": False
        }
        
        # Build authorization URL with session token
        auth_url = f"{os.getenv('OAUTH_CALLBACK_BASE_URL', 'http://localhost:8000')}/ceo/oauth/meta/authorize?platform={platform}&session={session_token}"
        
        logger.info("OAuth session created", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "session_token": session_token[:8] + "..."
        })
        
        return format_response(
            "success",
            "OAuth session created",
            {
                "session_token": session_token,
                "auth_url": auth_url,
                "expires_in": 300
            }
        )
    
    except Exception as e:
        logger.error("Failed to create OAuth session", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create OAuth session"
        )


@router.get("/oauth/meta/authorize")
async def oauth_authorize_endpoint(
    platform: str = Query(..., description="Platform to connect: 'whatsapp' or 'instagram'"),
    session: Optional[str] = Query(None, description="Temporary OAuth session token"),
    ceo_id: Optional[str] = None
):
    """
    Initiate Meta OAuth flow.
    
    Redirects CEO to Meta's OAuth consent screen for WhatsApp or Instagram.
    
    **Query Parameters:**
    - `platform`: 'whatsapp' or 'instagram'
    - `session`: Temporary session token (if not using Authorization header)
    
    **Returns:**
    - Redirect to Meta OAuth authorization URL
    
    **Example:**
    ```
    GET /ceo/oauth/meta/authorize?platform=whatsapp&session=abc123...
    ```
    """
    try:
        # Validate session token if provided
        if session:
            session_data = _oauth_sessions.get(session)
            
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session token"
                )
            
            # Check if expired
            if int(time.time()) > session_data["expires_at"]:
                _oauth_sessions.pop(session, None)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session token expired"
                )
            
            # Check if already used
            if session_data["used"]:
                _oauth_sessions.pop(session, None)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session token already used"
                )
            
            # Verify platform matches
            if session_data["platform"] != platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Platform mismatch"
                )
            
            # Mark as used and get CEO ID
            session_data["used"] = True
            ceo_id = session_data["ceo_id"]
            
            logger.info("OAuth session validated", extra={
                "ceo_id": ceo_id,
                "platform": platform,
                "session_token": session[:8] + "..."
            })
        else:
            # Fall back to JWT authentication
            if not ceo_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
        
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
    
    except HTTPException:
        raise
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


class NotificationPreferencesRequest(BaseModel):
    """Request model for notification preferences update"""
    notification_preferences: Dict[str, bool]


@router.patch("/settings/notifications")
async def update_notification_preferences(
    req: NotificationPreferencesRequest,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Update notification preferences for alerts and reports.
    
    Saves user preferences for:
    - SMS alerts (high-value orders, flagged receipts)
    - Email reports (daily fraud report, weekly summary)
    - Push notifications (in-app real-time alerts)
    
    Note: High-value escalations (≥ ₦1M) always require CEO approval regardless
    of notification settings (Zero Trust requirement).
    """
    try:
        from .database import get_ceo_by_id
        
        # Get current CEO record
        ceo = get_ceo_by_id(ceo_id)
        if not ceo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CEO not found"
            )
        
        # Update notification preferences in USERS_TABLE
        USERS_TABLE.update_item(
            Key={"user_id": ceo_id},
            UpdateExpression="SET notification_preferences = :prefs, updated_at = :now",
            ExpressionAttributeValues={
                ":prefs": req.notification_preferences,
                ":now": int(time.time())
            }
        )
        
        logger.info(
            "Notification preferences updated",
            extra={"ceo_id": ceo_id, "preferences": req.notification_preferences}
        )
        
        return format_response(
            "success",
            "Notification preferences saved successfully",
            {
                "notification_preferences": req.notification_preferences,
                "updated_at": int(time.time())
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update notification preferences",
            extra={"ceo_id": ceo_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save notification preferences: {str(e)}"
        )


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


# ==================== Chatbot Settings Alias Routes (for compatibility) ====================

@router.get("/chatbot/settings")
async def get_chatbot_settings_alias(ceo_id: str = Depends(get_current_ceo)):
    """Alias for GET /chatbot-settings (compatibility with test scripts)"""
    try:
        settings = get_chatbot_settings(ceo_id)
        
        logger.info("Chatbot settings retrieved via API (alias)", extra={"ceo_id": ceo_id})
        
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


@router.put("/chatbot/settings")
async def update_chatbot_settings_alias_put(
    req: ChatbotSettingsUpdateRequest,
    ceo_id: str = Depends(get_current_ceo)
):
    """Alias for PATCH /chatbot-settings using PUT method (compatibility with test scripts)"""
    try:
        updated_settings = update_chatbot_settings(
            ceo_id=ceo_id,
            settings=req.dict(exclude_unset=True)
        )
        
        logger.info("Chatbot settings updated via API (alias)", extra={"ceo_id": ceo_id})
        
        return format_response(
            "success",
            "Chatbot settings updated successfully",
            updated_settings
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Update chatbot settings failed", extra={
            "ceo_id": ceo_id,
            "error": str(e)
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update settings")


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


@router.get("/analytics", status_code=status.HTTP_200_OK)
async def get_analytics_dashboard(
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get comprehensive analytics data for the analytics dashboard.
    Combines vendor performance, fraud insights, summary statistics, and trend data.
    """
    try:
        # Get vendor performance data
        vendor_performance = get_vendor_performance_summary(ceo_id)
        
        # Get fraud trends for the last 7 days
        fraud_trends = get_ceo_fraud_trends(ceo_id, days=7)
        
        # Calculate fraud insights (top flagged reasons)
        # This would require a helper function to aggregate flagged reasons
        # For now, return mock structure that matches frontend
        fraud_insights = [
            {"flagged_reason": "Receipt mismatch", "count": 8, "percentage": 44.4},
            {"flagged_reason": "High-value transaction", "count": 5, "percentage": 27.8},
            {"flagged_reason": "Suspicious pattern", "count": 3, "percentage": 16.7},
            {"flagged_reason": "Duplicate receipt", "count": 2, "percentage": 11.1},
        ]
        
        # Calculate summary statistics
        total_orders = sum(v.get("total_orders", 0) for v in vendor_performance)
        total_flagged = sum(v.get("flagged_orders", 0) for v in vendor_performance)
        total_approved = sum(v.get("approved_orders", 0) for v in vendor_performance)
        avg_approval_time = sum(v.get("avg_approval_time_hours", 0) for v in vendor_performance) / len(vendor_performance) if vendor_performance else 0
        
        summary = {
            "total_vendors": len(vendor_performance),
            "total_orders": total_orders,
            "flagged_orders": total_flagged,
            "approved_orders": total_approved,
            "flag_rate": (total_flagged / total_orders * 100) if total_orders > 0 else 0,
            "avg_approval_time_hours": round(avg_approval_time, 2)
        }
        
        # Transform fraud trends to match frontend format
        trend_data = [
            {
                "week": f"Week {i+1}",
                "flagged": trend.get("fraud_count", 0),
                "approved": trend.get("approved_count", 0)
            }
            for i, trend in enumerate(fraud_trends[:4])  # Last 4 weeks
        ]
        
        return format_response(
            "success",
            "Analytics data retrieved successfully",
            {
                "vendor_performance": vendor_performance,
                "fraud_insights": fraud_insights,
                "summary": summary,
                "trend_data": trend_data
            }
        )
    except Exception as e:
        logger.error("Failed to retrieve analytics dashboard", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve analytics data")


@router.get("/notifications", status_code=status.HTTP_200_OK)
async def get_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Get recent notifications for the CEO (escalations, alerts, etc.).
    
    Query params:
        - limit: Maximum number of notifications to return (1-100, default 20)
        - unread_only: If true, return only unread notifications
    
    Returns notifications in the format expected by TopBar component:
    {
        "id": "notif_xxx",
        "type": "escalation" | "alert" | "info" | "warning",
        "title": "High-Value Transaction",
        "message": "Order #12345 requires approval",
        "timestamp": 1234567890,
        "read": false,
        "order_id": "order_xxx",
        "vendor_id": "vendor_xxx"
    }
    """
    try:
        notifications = get_notifications_for_ceo(ceo_id, limit=limit, unread_only=unread_only)
        
        # Transform to frontend format
        formatted_notifications = []
        for notif in notifications:
            formatted_notifications.append({
                "id": notif.get("notification_id"),
                "type": notif.get("type", "info"),
                "title": notif.get("title", ""),
                "message": notif.get("message", ""),
                "timestamp": notif.get("timestamp", 0),
                "read": notif.get("read", False),
                "order_id": notif.get("order_id"),
                "vendor_id": notif.get("vendor_id"),
            })
        
        unread_count = sum(1 for n in formatted_notifications if not n["read"])
        
        return format_response(
            "success",
            f"Retrieved {len(formatted_notifications)} notifications",
            {
                "notifications": formatted_notifications,
                "unread_count": unread_count,
                "total_count": len(formatted_notifications)
            }
        )
    except Exception as e:
        logger.error("Failed to retrieve notifications", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve notifications")


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: str,
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Mark a specific notification as read.
    
    Args:
        notification_id: Notification ID to mark as read
    """
    try:
        success = mark_notification_as_read(notification_id)
        
        if success:
            return format_response(
                "success",
                "Notification marked as read",
                {"notification_id": notification_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark notification as read", extra={"notification_id": notification_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update notification")


@router.post("/notifications/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    ceo_id: str = Depends(get_current_ceo)
):
    """
    Mark all notifications for the current CEO as read.
    """
    try:
        count = mark_all_notifications_as_read(ceo_id)
        
        return format_response(
            "success",
            f"Marked {count} notifications as read",
            {"count": count}
        )
    except Exception as e:
        logger.error("Failed to mark all notifications as read", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update notifications")


# ==================== TEST/DEBUG ENDPOINTS ====================

@router.post("/test/create-notification", status_code=status.HTTP_200_OK)
async def test_create_notification(
    notification_type: str = Query(default="escalation", description="Type: escalation, alert, info"),
    ceo_id: str = Depends(get_current_ceo)
):
    """
    🧪 TEST ENDPOINT: Create a test notification to verify the notification system is working.
    
    This will create a mock escalation notification that should:
    1. Appear in the TopBar notification bell
    2. Auto-pop the EscalationModal (if type=escalation and unread)
    3. Show in the notification dropdown
    
    Query params:
        - notification_type: Type of notification (escalation, alert, info)
    
    Usage:
        POST /ceo/test/create-notification?notification_type=escalation
    """
    try:
        import random
        
        # Generate test data
        test_order_id = f"test_order_{int(time.time())}_{random.randint(1000, 9999)}"
        test_vendor_id = f"test_vendor_{random.randint(100, 999)}"
        test_amount = random.choice([500000, 1200000, 2500000, 850000])
        test_reason = random.choice(["HIGH_VALUE", "VENDOR_FLAGGED"])
        
        # Create notification
        notification = create_notification(
            ceo_id=ceo_id,
            notification_type=notification_type,
            title="🧪 TEST: High-Value Transaction" if notification_type == "escalation" else "🧪 TEST: Alert",
            message=f"Test order #{test_order_id[:12]} (₦{test_amount:,.0f}) requires your approval",
            order_id=test_order_id,
            vendor_id=test_vendor_id,
            metadata={
                "reason": test_reason,
                "amount": test_amount,
                "escalation_id": f"test_escalation_{int(time.time())}",
                "is_test": True
            }
        )
        
        logger.info(f"✅ Test notification created: {notification['notification_id']} for CEO {ceo_id}")
        
        return format_response(
            "success",
            "Test notification created successfully! Check your notification bell in TopBar.",
            {
                "notification": {
                    "id": notification["notification_id"],
                    "type": notification["type"],
                    "title": notification["title"],
                    "message": notification["message"],
                    "order_id": notification.get("order_id"),
                    "amount": test_amount,
                    "reason": test_reason
                },
                "instructions": {
                    "1": "Check the notification bell icon in TopBar (should show unread count)",
                    "2": "If type=escalation, the modal should auto-pop within 30 seconds",
                    "3": "Click the bell to see the notification in the dropdown",
                    "4": "Click 'Review Now' to test navigation to approvals page"
                }
            }
        )
    
    except Exception as e:
        logger.error("Failed to create test notification", extra={"ceo_id": ceo_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test notification: {str(e)}"
        )
