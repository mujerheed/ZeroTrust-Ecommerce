"""
FastAPI routes for receipt upload and verification.

Endpoints:
- POST /receipts/request-upload - Generate presigned URL for buyer
- POST /receipts/confirm-upload - Confirm upload completion
- GET /receipts/{receipt_id} - Get receipt details (authorized users)
- GET /vendor/receipts/pending - List pending receipts for vendor
- POST /vendor/receipts/{receipt_id}/verify - Vendor verifies receipt
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, Literal
from .receipt_logic import (
    request_receipt_upload,
    confirm_receipt_upload,
    vendor_verify_receipt,
    get_vendor_pending_receipts,
    get_receipt_details
)
from vendor_service.utils import verify_vendor_token
from ceo_service.utils import verify_ceo_token
from common.logger import logger

router = APIRouter()
security = HTTPBearer()


# ==================== REQUEST MODELS ====================

class RequestUploadRequest(BaseModel):
    """Request model for generating presigned upload URL."""
    order_id: str
    buyer_id: str
    vendor_id: str
    ceo_id: str
    file_extension: str  # jpg, png, pdf
    content_type: str  # image/jpeg, image/png, application/pdf


class ConfirmUploadRequest(BaseModel):
    """Request model for confirming upload completion."""
    receipt_id: str
    s3_key: str
    order_id: str
    buyer_id: str
    vendor_id: str
    ceo_id: str


class VerifyReceiptRequest(BaseModel):
    """Request model for vendor verification."""
    action: Literal['approve', 'reject', 'flag']
    notes: Optional[str] = None


# ==================== RECEIPT UPLOAD ENDPOINTS ====================

@router.post("/request-upload", status_code=status.HTTP_200_OK)
async def request_upload(req: RequestUploadRequest):
    """
    Generate presigned S3 URL for buyer to upload receipt.
    
    Security:
    - URL expires in 5 minutes
    - Content-type validation
    - File size limit (5MB)
    - Server-side encryption enabled
    """
    try:
        result = request_receipt_upload(
            order_id=req.order_id,
            buyer_id=req.buyer_id,
            vendor_id=req.vendor_id,
            ceo_id=req.ceo_id,
            file_extension=req.file_extension,
            content_type=req.content_type
        )
        
        return {
            "status": "success",
            "message": "Upload URL generated",
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Invalid upload request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/confirm-upload", status_code=status.HTTP_201_CREATED)
async def confirm_upload(req: ConfirmUploadRequest):
    """
    Confirm receipt upload and save metadata to DynamoDB.
    
    Called by buyer after successful upload to S3.
    """
    try:
        result = confirm_receipt_upload(
            receipt_id=req.receipt_id,
            s3_key=req.s3_key,
            order_id=req.order_id,
            buyer_id=req.buyer_id,
            vendor_id=req.vendor_id,
            ceo_id=req.ceo_id
        )
        
        return {
            "status": "success",
            "message": result['message'],
            "data": {
                "receipt_id": result['receipt_id'],
                "status": result['status']
            }
        }
    
    except ValueError as e:
        logger.warning(f"Invalid confirm upload request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to confirm upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{receipt_id}", status_code=status.HTTP_200_OK)
async def get_receipt(receipt_id: str, token: str = Depends(security)):
    """
    Get receipt details with download URL.
    
    Authorization:
    - Buyer who uploaded it
    - Vendor assigned to review
    - CEO for the business
    
    Requires JWT token in Authorization header.
    """
    try:
        # For now, we'll accept any valid token (Buyer/Vendor/CEO)
        # In production, decode JWT to get user_id and role
        # This is a simplified version
        
        # Mock: extract from token (replace with actual JWT decode)
        # user_id = "vendor_123"
        # user_role = "Vendor"
        
        # For demo purposes, allow access with receipt_id only
        # In production, verify token and check authorization
        
        result = get_receipt_details(
            receipt_id=receipt_id,
            user_id="vendor_123",  # TODO: Extract from JWT
            user_role="Vendor"  # TODO: Extract from JWT
        )
        
        return {
            "status": "success",
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Receipt access denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== VENDOR VERIFICATION ENDPOINTS ====================

@router.get("/vendor/receipts/pending", status_code=status.HTTP_200_OK)
async def get_pending_receipts(token: str = Depends(security), limit: int = 50):
    """
    Get all pending receipts for vendor to review.
    
    Requires vendor JWT token.
    """
    try:
        vendor_id = verify_vendor_token(token.credentials)
        if not vendor_id:
            raise HTTPException(status_code=401, detail="Invalid vendor token")
        
        result = get_vendor_pending_receipts(vendor_id, limit=limit)
        
        return {
            "status": "success",
            "data": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pending receipts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/vendor/receipts/{receipt_id}/verify", status_code=status.HTTP_200_OK)
async def verify_receipt(receipt_id: str, req: VerifyReceiptRequest, token: str = Depends(security)):
    """
    Vendor verifies receipt (approve/reject/flag).
    
    Auto-escalation logic:
    - Amount ≥ ₦1,000,000 + approve → escalates to CEO
    - Flagged → escalates to CEO
    - Otherwise → processed by vendor
    
    Requires vendor JWT token.
    """
    try:
        vendor_id = verify_vendor_token(token.credentials)
        if not vendor_id:
            raise HTTPException(status_code=401, detail="Invalid vendor token")
        
        result = vendor_verify_receipt(
            receipt_id=receipt_id,
            vendor_id=vendor_id,
            action=req.action,
            notes=req.notes
        )
        
        return {
            "status": "success",
            "message": result['message'],
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Invalid verification request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
