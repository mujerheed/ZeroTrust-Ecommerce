"""
Complete FastAPI routes for vendor dashboard functionality.
All endpoints require vendor JWT authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from vendor_logic import (
    get_vendor_dashboard_data, get_vendor_orders, get_order_details,
    verify_receipt, get_receipt_details, search_vendor_orders
)
from utils import format_response, verify_vendor_token

router = APIRouter()
security = HTTPBearer()

def get_current_vendor(token: str = Depends(security)) -> str:
    """Extract and verify vendor_id from JWT token."""
    vendor_id = verify_vendor_token(token.credentials)
    if not vendor_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return vendor_id

# ========== VENDOR DASHBOARD ==========
@router.get("/dashboard")
async def get_dashboard(vendor_id: str = Depends(get_current_vendor)):
    """Get complete vendor dashboard data."""
    try:
        dashboard_data = get_vendor_dashboard_data(vendor_id)
        return format_response("success", "Dashboard data retrieved", dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========== ORDER MANAGEMENT ==========
@router.get("/orders")
async def get_orders(
    status: Optional[str] = None,
    limit: int = 50,
    vendor_id: str = Depends(get_current_vendor)
):
    """Get vendor's assigned orders with optional status filtering."""
    try:
        orders = get_vendor_orders(vendor_id, status, limit)
        return format_response("success", f"Retrieved {len(orders)} orders", {
            "orders": orders,
            "filter_applied": status,
            "total_count": len(orders)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders/{order_id}")
async def get_order(order_id: str, vendor_id: str = Depends(get_current_vendor)):
    """Get detailed information about a specific order."""
    try:
        order_details = get_order_details(vendor_id, order_id)
        return format_response("success", "Order details retrieved", order_details)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ========== RECEIPT VERIFICATION ==========
class ReceiptVerificationRequest(BaseModel):
    verification_status: str  # 'verified' or 'flagged'
    notes: Optional[str] = None

@router.post("/orders/{order_id}/verify")
async def verify_order_receipt(
    order_id: str,
    req: ReceiptVerificationRequest,
    vendor_id: str = Depends(get_current_vendor)
):
    """Verify or flag a receipt for an order."""
    try:
        result = verify_receipt(vendor_id, order_id, req.verification_status, req.notes)
        return format_response("success", result["message"], result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/receipts/{order_id}")
async def get_receipt(order_id: str, vendor_id: str = Depends(get_current_vendor)):
    """Get detailed receipt information for verification."""
    try:
        receipt_details = get_receipt_details(vendor_id, order_id)
        return format_response("success", "Receipt details retrieved", receipt_details)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ========== SEARCH FUNCTIONALITY ==========
@router.get("/search")
async def search_orders(
    q: str,
    field: str = "buyer_name",
    vendor_id: str = Depends(get_current_vendor)
):
    """Search through vendor's orders."""
    try:
        if len(q) < 2:
            raise ValueError("Search term must be at least 2 characters")
        
        results = search_vendor_orders(vendor_id, q, field)
        return format_response("success", f"Found {len(results)} matching orders", {
            "results": results,
            "search_term": q,
            "search_field": field
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========== VENDOR STATISTICS ==========
@router.get("/stats")
async def get_stats(vendor_id: str = Depends(get_current_vendor)):
    """Get vendor performance statistics."""
    try:
        dashboard_data = get_vendor_dashboard_data(vendor_id)
        return format_response("success", "Statistics retrieved", {
            "stats": dashboard_data["statistics"]
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
