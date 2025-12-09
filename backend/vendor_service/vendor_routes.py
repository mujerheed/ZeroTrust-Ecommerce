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
from common.logger import logger

router = APIRouter()
security = HTTPBearer()

def get_current_vendor(token: str = Depends(security)) -> str:
    """Extract and verify vendor_id from JWT token."""
    vendor_id = verify_vendor_token(token.credentials)
    if not vendor_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return vendor_id


# ========== REQUEST MODELS ==========

class VendorChatSendRequest(BaseModel):
    """Request model for sending messages to buyers."""
    buyer_id: str
    message: str
    order_id: Optional[str] = None


# ========== VENDOR DASHBOARD ==========
@router.get("/dashboard")
async def get_dashboard(vendor_id: str = Depends(get_current_vendor)):
    """Get complete vendor dashboard data."""
    try:
        dashboard_data = get_vendor_dashboard_data(vendor_id)
        return format_response("success", "Dashboard data retrieved", dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== VENDOR CHAT RELAY ==========
@router.post("/chat/send")
async def send_message_to_buyer(
    req: VendorChatSendRequest,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Send message to buyer via WhatsApp or Instagram.
    
    This is the main endpoint for vendor-to-buyer communication.
    
    Body:
        - buyer_id: Buyer ID (wa_... or ig_...)
        - message: Message text (max 500 chars)
        - order_id: Optional order ID for context
    
    Returns:
        {
            "message_id": "wamid.xxx",
            "platform": "whatsapp" | "instagram",
            "status": "sent",
            "sent_at": 1733654400
        }
    """
    try:
        from .database import get_vendor
        from .chat_logic import (
            send_vendor_message_to_buyer,
            validate_buyer_belongs_to_ceo,
            save_vendor_message_to_audit
        )
        
        # Get vendor details
        vendor = get_vendor(vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        ceo_id = vendor.get("ceo_id")
        vendor_name = vendor.get("name", "Vendor")
        
        if not ceo_id:
            raise HTTPException(status_code=400, detail="Vendor missing ceo_id")
        
        # Validate buyer belongs to same CEO
        if not validate_buyer_belongs_to_ceo(req.buyer_id, ceo_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Buyer does not belong to your business"
            )
        
        # Send message
        result = await send_vendor_message_to_buyer(
            vendor_id=vendor_id,
            buyer_id=req.buyer_id,
            message=req.message,
            ceo_id=ceo_id,
            order_id=req.order_id,
            vendor_name=vendor_name
        )
        
        # Save to audit log
        save_vendor_message_to_audit(
            vendor_id=vendor_id,
            buyer_id=req.buyer_id,
            message=req.message,
            order_id=req.order_id,
            ceo_id=ceo_id,
            platform=result.get("platform"),
            message_id=result.get("message_id")
        )
        
        return format_response("success", "Message sent successfully", result)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send vendor message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


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


@router.get("/notifications/recent")
async def get_recent_notification_events(
    since: int = 0,  # Unix timestamp
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Get recent notification events since a timestamp for real-time toast alerts.
    
    Frontend polls this every 15 seconds with last check timestamp.
    
    Query Parameters:
        since: Unix timestamp (seconds) of last check
    
    Returns:
        {
            "events": [
                {
                    "type": "new_order" | "receipt_uploaded" | "order_flagged" | "high_value_alert",
                    "order_id": "ord_123",
                    "buyer_id": "wa_234...",
                    "amount": 12500,
                    "timestamp": 1732012345
                },
                ...
            ]
        }
    """
    try:
        from .database import get_vendor_assigned_orders
        import time
        
        # Get orders updated since 'since' timestamp
        all_orders = get_vendor_assigned_orders(vendor_id, status=None)
        recent_orders = [
            order for order in all_orders
            if order.get("updated_at", 0) > since
        ]
        
        # Generate events based on order status changes
        events = []
        for order in recent_orders:
            order_status = order.get("order_status", "")
            amount = order.get("total_amount", 0)
            
            # Determine event type based on status and amount
            if order_status == "PENDING" and order.get("created_at", 0) > since:
                events.append({
                    "type": "new_order",
                    "order_id": order.get("order_id"),
                    "buyer_id": order.get("buyer_id"),
                    "amount": amount,
                    "timestamp": order.get("created_at")
                })
            elif order_status == "RECEIPT_UPLOADED":
                events.append({
                    "type": "receipt_uploaded",
                    "order_id": order.get("order_id"),
                    "buyer_id": order.get("buyer_id"),
                    "amount": amount,
                    "timestamp": order.get("updated_at")
                })
            elif order_status == "FLAGGED":
                events.append({
                    "type": "order_flagged",
                    "order_id": order.get("order_id"),
                    "buyer_id": order.get("buyer_id"),
                    "amount": amount,
                    "timestamp": order.get("updated_at")
                })
            elif amount >= 100000000:  # ₦1M threshold (in kobo)
                events.append({
                    "type": "high_value_alert",
                    "order_id": order.get("order_id"),
                    "buyer_id": order.get("buyer_id"),
                    "amount": amount,
                    "timestamp": order.get("updated_at")
                })
        
        # Sort by timestamp descending (most recent first)
        events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return format_response("success", f"{len(events)} recent events", {
            "events": events[:20],  # Limit to 20 most recent
            "check_timestamp": int(time.time())
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent notifications: {str(e)}")


# ========== BUYERS MANAGEMENT ==========

@router.get("/buyers")
async def get_buyers(
    flag_status: Optional[str] = None,  # 'flagged', 'clean', None for all
    limit: int = 50,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Get all buyers this vendor has interacted with.
    
    Query params:
        - flag_status: Filter by flag status ('flagged', 'clean', or None for all)
        - limit: Max results to return (default 50)
    
    Returns:
        {
            "buyers": [
                {
                    "buyer_id": "wa_234...",
                    "name": "John Doe",
                    "phone": "+234***5678",
                    "total_orders": 3,
                    "last_interaction": 1732012345,
                    "flag_status": "clean",
                    "flagged_count": 0
                }
            ],
            "total_count": number,
            "filter_applied": "flagged" or None
        }
    """
    try:
        from .database import get_vendor_assigned_orders
        from collections import defaultdict
        import time
        
        # Get all orders for this vendor
        all_orders = get_vendor_assigned_orders(vendor_id, status=None)
        
        # Group by buyer_id
        buyer_stats = defaultdict(lambda: {
            "total_orders": 0,
            "last_interaction": 0,
            "flagged_count": 0,
            "buyer_id": None,
            "phone": None
        })
        
        for order in all_orders:
            buyer_id = order.get("buyer_id")
            if not buyer_id:
                continue
            
            buyer_stats[buyer_id]["buyer_id"] = buyer_id
            buyer_stats[buyer_id]["phone"] = order.get("buyer_phone", "Unknown")
            buyer_stats[buyer_id]["total_orders"] += 1
            buyer_stats[buyer_id]["last_interaction"] = max(
                buyer_stats[buyer_id]["last_interaction"],
                order.get("updated_at", 0)
            )
            
            if order.get("order_status") == "FLAGGED":
                buyer_stats[buyer_id]["flagged_count"] += 1
        
        # Convert to list and add computed fields
        buyers_list = []
        for buyer_id, stats in buyer_stats.items():
            # Determine flag status
            flag_stat = "flagged" if stats["flagged_count"] > 0 else "clean"
            
            # Apply filter if specified
            if flag_status and flag_stat != flag_status:
                continue
            
            # Mask phone (show last 4 digits only)
            phone = stats["phone"]
            if phone and len(phone) > 4:
                masked_phone = f"+234***{phone[-4:]}"
            else:
                masked_phone = phone
            
            buyers_list.append({
                "buyer_id": buyer_id,
                "name": f"Buyer {buyer_id[-6:]}",  # Generate display name from ID
                "phone": masked_phone,
                "total_orders": stats["total_orders"],
                "last_interaction": stats["last_interaction"],
                "last_interaction_ago": _time_ago(stats["last_interaction"]),
                "flag_status": flag_stat,
                "flagged_count": stats["flagged_count"]
            })
        
        # Sort by last interaction (most recent first)
        buyers_list.sort(key=lambda x: x["last_interaction"], reverse=True)
        
        # Apply limit
        buyers_list = buyers_list[:limit]
        
        return format_response("success", f"Retrieved {len(buyers_list)} buyers", {
            "buyers": buyers_list,
            "total_count": len(buyers_list),
            "filter_applied": flag_status
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve buyers: {str(e)}")


@router.get("/buyers/{buyer_id}")
async def get_buyer_details(
    buyer_id: str,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Get detailed information about a specific buyer.
    
    Returns:
        {
            "buyer_id": "wa_234...",
            "phone": "+234***5678",
            "total_orders": 5,
            "completed_orders": 3,
            "flagged_orders": 1,
            "pending_orders": 1,
            "first_order_date": 1730012345,
            "last_order_date": 1732012345,
            "orders": [...]  // Recent orders
        }
    """
    try:
        from .database import get_vendor_assigned_orders
        
        # Get all orders for this buyer from this vendor
        all_orders = get_vendor_assigned_orders(vendor_id, status=None)
        buyer_orders = [o for o in all_orders if o.get("buyer_id") == buyer_id]
        
        if not buyer_orders:
            raise HTTPException(status_code=404, detail=f"Buyer {buyer_id} not found or no orders with this vendor")
        
        # Calculate stats
        total = len(buyer_orders)
        completed = sum(1 for o in buyer_orders if o.get("order_status") in ["APPROVED", "CEO_APPROVED", "COMPLETED"])
        flagged = sum(1 for o in buyer_orders if o.get("order_status") == "FLAGGED")
        pending = sum(1 for o in buyer_orders if o.get("order_status") in ["PENDING", "RECEIPT_UPLOADED"])
        
        timestamps = [o.get("created_at", 0) for o in buyer_orders if o.get("created_at")]
        first_order = min(timestamps) if timestamps else 0
        last_order = max(timestamps) if timestamps else 0
        
        # Get phone from first order
        phone = buyer_orders[0].get("buyer_phone", "Unknown")
        if phone and len(phone) > 4:
            masked_phone = f"+234***{phone[-4:]}"
        else:
            masked_phone = phone
        
        # Sort orders by date (most recent first) and limit to 10
        buyer_orders.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        recent_orders = buyer_orders[:10]
        
        return format_response("success", "Buyer details retrieved", {
            "buyer_id": buyer_id,
            "phone": masked_phone,
            "total_orders": total,
            "completed_orders": completed,
            "flagged_orders": flagged,
            "pending_orders": pending,
            "first_order_date": first_order,
            "last_order_date": last_order,
            "orders": recent_orders
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve buyer details: {str(e)}")


# ========== NEGOTIATION / CHAT INTERFACE ==========

class ChatMessageRequest(BaseModel):
    message: str
    quick_action: Optional[str] = None  # 'confirm_price', 'send_payment_details', 'request_receipt'


@router.post("/orders/{order_id}/messages")
async def send_chat_message(
    order_id: str,
    req: ChatMessageRequest,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Send a chat message to buyer for an order (negotiation interface).
    
    Body:
        - message: Text message to send
        - quick_action: Optional quick action ('confirm_price', 'send_payment_details', 'request_receipt')
    
    Returns:
        {
            "message_id": "msg_123",
            "sent_at": 1732012345,
            "delivery_status": "sent" | "delivered" | "failed"
        }
    """
    try:
        from .database import get_order_by_id, get_vendor
        from .chat_logic import send_vendor_message_to_buyer, save_vendor_message_to_audit
        import time
        
        # Verify order belongs to this vendor
        order = get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if order.get("vendor_id") != vendor_id:
            raise HTTPException(status_code=403, detail="Access denied: Order does not belong to you")
        
        buyer_id = order.get("buyer_id")
        ceo_id = order.get("ceo_id")
        
        if not buyer_id or not ceo_id:
            raise HTTPException(status_code=400, detail="Order missing buyer_id or ceo_id")
        
        # Get vendor details for name attribution
        vendor = get_vendor(vendor_id)
        vendor_name = vendor.get("name", "Vendor") if vendor else "Vendor"
        
        # Build message text
        message_text = req.message
        
        # Handle quick actions
        if req.quick_action == "confirm_price":
            amount = order.get("total_amount", 0)
            message_text = f"✅ Price confirmed: ₦{amount:,.2f}\n\nPlease proceed with payment to the account details provided."
        
        elif req.quick_action == "send_payment_details":
            # Get vendor's bank details from vendor profile
            bank_name = vendor.get("bank_name", "Access Bank") if vendor else "Access Bank"
            account_number = vendor.get("account_number", "0123456789") if vendor else "0123456789"
            account_name = vendor.get("account_name", vendor_name) if vendor else vendor_name
            
            message_text = (
                f"💳 *Payment Details*\n\n"
                f"Bank: {bank_name}\n"
                f"Account: {account_number}\n"
                f"Name: {account_name}\n"
                f"Amount: ₦{order.get('total_amount', 0):,.2f}\n"
                f"Reference: {order_id}\n\n"
                "Please send payment receipt after transfer."
            )
        
        elif req.quick_action == "request_receipt":
            message_text = "📸 Please upload your payment receipt to complete this order. You can send it directly in this chat."
        
        # Send message via Meta API
        result = await send_vendor_message_to_buyer(
            vendor_id=vendor_id,
            buyer_id=buyer_id,
            message=message_text,
            ceo_id=ceo_id,
            order_id=order_id,
            vendor_name=vendor_name
        )
        
        # Save to audit log
        save_vendor_message_to_audit(
            vendor_id=vendor_id,
            buyer_id=buyer_id,
            message=message_text,
            order_id=order_id,
            ceo_id=ceo_id,
            platform=result.get("platform"),
            message_id=result.get("message_id")
        )
        
        return format_response("success", "Message sent to buyer", {
            "message_id": result.get("message_id"),
            "sent_at": result.get("sent_at"),
            "delivery_status": result.get("status"),
            "platform": result.get("platform"),
            "quick_action_applied": req.quick_action
        })
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/orders/{order_id}/messages")
async def get_chat_history(
    order_id: str,
    limit: int = 50,
    vendor_id: str = Depends(get_current_vendor)
):
    """
    Get chat history for an order (negotiation interface).
    
    Query params:
        - limit: Max messages to return (default 50)
    
    Returns:
        {
            "messages": [
                {
                    "message_id": "msg_123",
                    "sender": "buyer" | "vendor",
                    "text": "Hello, is this available?",
                    "timestamp": 1732012345,
                    "time_ago": "2h ago"
                }
            ],
            "total_count": number
        }
    """
    try:
        from .database import get_order_by_id
        
        # Verify order belongs to this vendor
        order = get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if order.get("vendor_id") != vendor_id:
            raise HTTPException(status_code=403, detail="Access denied: Order does not belong to you")
        
        # TODO: Fetch actual chat history from database or Meta API
        # For now, return mock data
        messages = [
            {
                "message_id": "msg_001",
                "sender": "buyer",
                "text": "Hello, is this dress still available?",
                "timestamp": 1732000000,
                "time_ago": _time_ago(1732000000)
            },
            {
                "message_id": "msg_002",
                "sender": "vendor",
                "text": "Yes, it's available. The price is ₦12,500.",
                "timestamp": 1732000300,
                "time_ago": _time_ago(1732000300)
            },
            {
                "message_id": "msg_003",
                "sender": "buyer",
                "text": "Can you do ₦11,000?",
                "timestamp": 1732000600,
                "time_ago": _time_ago(1732000600)
            },
            {
                "message_id": "msg_004",
                "sender": "vendor",
                "text": "Best price is ₦12,000. Final offer.",
                "timestamp": 1732000900,
                "time_ago": _time_ago(1732000900)
            }
        ]
        
        return format_response("success", f"Retrieved {len(messages)} messages", {
            "messages": messages,
            "total_count": len(messages),
            "order_id": order_id
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")


# ========== UTILITY FUNCTIONS ==========

def _time_ago(timestamp: int) -> str:
    """Convert Unix timestamp to human-readable time ago string."""
    import time
    
    if timestamp == 0:
        return "Never"
    
    diff = int(time.time()) - timestamp
    
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        minutes = diff // 60
        return f"{minutes}m ago"
    elif diff < 86400:
        hours = diff // 3600
        return f"{hours}h ago"
    elif diff < 604800:
        days = diff // 86400
        return f"{days}d ago"
    else:
        weeks = diff // 604800
        return f"{weeks}w ago"
