"""
FastAPI routes for CEO admin operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from .ceo_logic import (
    initiate_ceo_signup, verify_ceo_signup,
    login_ceo, list_vendors, add_vendor,
    remove_vendor, view_flagged_orders,
    approve_transaction, decline_transaction,
    fetch_audit_logs
)
from .utils import format_response, verify_ceo_token

router   = APIRouter()
security = HTTPBearer()

def get_current_ceo(token=Depends(security)) -> str:
    ceo_id = verify_ceo_token(token.credentials)
    if not ceo_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return ceo_id

# CEO Signup and verification
class CEOSignupRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr

@router.post("/ceo/signup", status_code=201)
async def ceo_signup(req: CEOSignupRequest):
    """
    Initiate CEO signup: generate and send 6-char OTP.
    """
    ceo_id = initiate_ceo_signup(req.name, req.phone, req.email)
    return format_response("success", "OTP sent for CEO signup", {"ceo_id": ceo_id})

class CEOVerifySignupRequest(BaseModel):
    ceo_id: str
    otp: str
    settings: Optional[Dict[str, Any]] = {}  # optional chat template settings

@router.post("/ceo/verify-signup")
async def ceo_verify_signup(req: CEOVerifySignupRequest):
    """
    Verify signup OTP and create CEO account with optional settings.
    """
    try:
        created_id = verify_ceo_signup(req.ceo_id, req.otp, {
            "name": req.settings.get("name"),
            "phone": req.settings.get("phone"),
            "email": req.settings.get("email"),
            "settings": req.settings.get("settings", {})
        })
        return format_response("success", "CEO account created", {"ceo_id": created_id})
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
# Vendor Management
class VendorCreateRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr

@router.post("/vendors", status_code=status.HTTP_201_CREATED)
async def create_vendor_endpoint(req: VendorCreateRequest, ceo_id: str = Depends(get_current_ceo)):
    vid = add_vendor(req.name, req.phone, req.email, ceo_id)
    return format_response("success", "Vendor created", {"vendor_id": vid})

@router.get("/vendors", response_model=List[dict])
async def list_vendors_endpoint(ceo_id: str = Depends(get_current_ceo)):
    vendors = list_vendors()
    return format_response("success", "Vendors fetched", vendors)

@router.delete("/vendors/{vendor_id}")
async def delete_vendor_endpoint(vendor_id: str, ceo_id: str = Depends(get_current_ceo)):
    try:
        remove_vendor(vendor_id)
        return format_response("success", "Vendor removed")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Transaction Oversight
@router.get("/transactions/flagged")
async def flagged_orders_endpoint(ceo_id: str = Depends(get_current_ceo)):
    orders = view_flagged_orders()
    return format_response("success", "Flagged orders fetched", orders)

@router.post("/transactions/{order_id}/approve")
async def approve_transaction_endpoint(order_id: str, ceo_id: str = Depends(get_current_ceo)):
    approve_transaction(order_id, ceo_id)
    return format_response("success", "Transaction approved")

@router.post("/transactions/{order_id}/decline")
async def decline_transaction_endpoint(order_id: str, ceo_id: str = Depends(get_current_ceo)):
    decline_transaction(order_id, ceo_id)
    return format_response("success", "Transaction declined")

# Audit Log Access
@router.get("/audit-logs")
async def audit_logs_endpoint(limit: int = 100, ceo_id: str = Depends(get_current_ceo)):
    logs = fetch_audit_logs(limit)
    return format_response("success", "Audit logs fetched", logs)
