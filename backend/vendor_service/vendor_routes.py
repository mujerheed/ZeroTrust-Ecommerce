"""
Complete FastAPI routes for vendor dashboard functionality.
All endpoints require vendor JWT authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from .vendor_logic import (
    get_vendor_dashboard_data, get_vendor_orders, get_order_details,
    verify_receipt, get_receipt_details, search_vendor_orders
)
from .preferences import save_vendor_preferences, get_vendor_preferences
from common.analytics import get_vendor_orders_by_day
from .utils import format_response, verify_vendor_token

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


# ========== VENDOR PREFERENCES ==========

class VendorPreferencesUpdateRequest(BaseModel):
    auto_approve_threshold: Optional[int] = None  # Amount in kobo (e.g., 500000 = ₦5,000)
    textract_enabled: Optional[bool] = None


@router.get("/preferences")
async def get_preferences(vendor_id: str = Depends(get_current_vendor)):
    """
    Get vendor business preferences.
    
    Returns:
        - auto_approve_threshold: Amount in kobo (0 = disabled)
        - textract_enabled: Boolean
        - updated_at: Unix timestamp or None
    """
    try:
        preferences = get_vendor_preferences(vendor_id)
        return format_response("success", "Preferences retrieved", preferences)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve preferences: {str(e)}")


@router.put("/preferences")
async def update_preferences(
    req: VendorPreferencesUpdateRequest,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Update vendor business preferences.
    
    Body:
        - auto_approve_threshold: Optional[int] - Amount in kobo below which receipts auto-approve (0 = disabled, max ₦1M)
        - textract_enabled: Optional[bool] - Enable/disable Textract OCR verification
    
    Returns:
        Updated preferences record
    """
    try:
        updated_preferences = save_vendor_preferences(
            vendor_id=vendor_id,
            auto_approve_threshold=req.auto_approve_threshold,
            textract_enabled=req.textract_enabled
        )
        return format_response("success", "Preferences updated successfully", updated_preferences)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


# ========== ANALYTICS ==========

@router.get("/analytics/orders-by-day")
async def get_orders_by_day(
    days: int = 7,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Get daily order counts for the past N days.
    
    Query params:
        - days: Number of days to look back (default 7, max 90)
    
    Returns:
        Array of {date: "YYYY-MM-DD", count: number}
    """
    if days > 90:
        raise HTTPException(status_code=400, detail="Maximum days is 90")
    
    try:
        daily_data = get_vendor_orders_by_day(vendor_id, days)
        return format_response("success", f"Daily order data for past {days} days", {
            "data": daily_data,
            "days_requested": days,
            "total_orders": sum(d["count"] for d in daily_data)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


# ========== NOTIFICATIONS ==========

@router.get("/notifications/unread")
async def get_unread_notifications(vendor_id: str = Depends(get_current_vendor)):
    """
    Get count of unread notifications (new orders since last check).
    
    Frontend should poll this endpoint every 30 seconds for real-time updates.
    
    Returns:
        {
            "new_count": number,
            "notifications": [
                {
                    "order_id": "ord_123",
                    "buyer_id": "wa_234...",
                    "amount": 12500,
                    "status": "RECEIPT_UPLOADED",
                    "created_at": 1732012345
                },
                ...
            ]
        }
    """
    try:
        from .database import get_vendor, get_vendor_assigned_orders, USERS_TABLE
        import time
        
        # Get vendor's last_notif_check timestamp
        vendor = get_vendor(vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        last_check = vendor.get("last_notif_check", 0)
        
        # Get orders created or updated since last check
        all_orders = get_vendor_assigned_orders(vendor_id, status=None)
        new_orders = [
            order for order in all_orders
            if order.get("updated_at", 0) > last_check
        ]
        
        # Update last_notif_check timestamp
        USERS_TABLE.update_item(
            Key={"user_id": vendor_id},
            UpdateExpression="SET last_notif_check = :now",
            ExpressionAttributeValues={":now": int(time.time())}
        )
        
        # Format notifications
        notifications = []
        for order in new_orders[:10]:  # Limit to 10 most recent
            notifications.append({
                "order_id": order.get("order_id"),
                "buyer_id": order.get("buyer_id"),
                "amount": order.get("amount"),
                "status": order.get("order_status"),
                "created_at": order.get("created_at"),
                "updated_at": order.get("updated_at")
            })
        
        return format_response("success", f"{len(new_orders)} new notifications", {
            "new_count": len(new_orders),
            "notifications": notifications,
            "last_check_timestamp": int(time.time())
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notifications: {str(e)}")
