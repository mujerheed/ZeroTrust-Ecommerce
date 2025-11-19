"""
FastAPI routes for order management.

Endpoints:
- POST /orders - Create new order (vendor)
- GET /orders/{order_id} - Get order details (vendor/buyer)
- GET /orders - List orders (vendor with filters)
- PATCH /orders/{order_id}/confirm - Confirm order (buyer)
- PATCH /orders/{order_id}/cancel - Cancel order (buyer)
- PATCH /orders/{order_id}/receipt - Add receipt (buyer)
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from common.logger import logger
from .utils import format_response, verify_vendor_token, verify_buyer_token
from . import order_logic


# Pydantic models for request/response validation
class OrderItem(BaseModel):
    """Single order item."""
    name: str = Field(..., description="Item name", min_length=1)
    quantity: int = Field(..., description="Item quantity", gt=0)
    price: float = Field(..., description="Item price per unit", ge=0)
    description: Optional[str] = Field(None, description="Optional item description")


class CreateOrderRequest(BaseModel):
    """Request body for creating an order."""
    buyer_id: str = Field(..., description="Buyer identifier (wa_xxx or ig_xxx)")
    items: List[OrderItem] = Field(..., description="Order items", min_items=1)
    notes: Optional[str] = Field(None, description="Optional order notes")


class ConfirmOrderRequest(BaseModel):
    """Request body for confirming an order."""
    buyer_id: str = Field(..., description="Buyer identifier confirming the order")


class CancelOrderRequest(BaseModel):
    """Request body for cancelling an order."""
    buyer_id: str = Field(..., description="Buyer identifier cancelling the order")
    reason: Optional[str] = Field(None, description="Optional cancellation reason")


class AddReceiptRequest(BaseModel):
    """Request body for adding receipt to order."""
    buyer_id: str = Field(..., description="Buyer identifier uploading receipt")
    receipt_url: str = Field(..., description="S3 URL of uploaded receipt")


# Initialize router
router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=201)
async def create_order(
    request: CreateOrderRequest,
    authorization: str = Header(None)
):
    """
    Create a new order (Vendor only).
    
    Workflow:
    1. Verify vendor token
    2. Validate buyer exists and belongs to vendor's CEO
    3. Create order in DynamoDB
    4. Send notification to buyer via WhatsApp/Instagram
    5. Return order details
    
    **Authorization**: Vendor JWT token required
    
    **Request Body**:
    ```json
    {
        "buyer_id": "wa_2348012345678",
        "items": [
            {
                "name": "Product A",
                "quantity": 2,
                "price": 5000.00,
                "description": "Optional description"
            }
        ],
        "notes": "Optional order notes"
    }
    ```
    
    **Response** (201 Created):
    ```json
    {
        "status": "success",
        "message": "Order created successfully",
        "data": {
            "order_id": "ord_1700000000_a1b2c3d4",
            "vendor_id": "vendor_123",
            "buyer_id": "wa_2348012345678",
            "ceo_id": "ceo_456",
            "items": [...],
            "total_amount": 10000.00,
            "currency": "NGN",
            "status": "pending",
            "notification_sent": true,
            "created_at": 1700000000,
            "updated_at": 1700000000
        }
    }
    ```
    """
    try:
        # Verify vendor token
        vendor_payload = verify_vendor_token(authorization)
        vendor_id = vendor_payload.get("sub")  # sub = user_id
        ceo_id = vendor_payload.get("ceo_id")
        
        if not vendor_id or not ceo_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing vendor_id or ceo_id")
        
        # Convert Pydantic models to dicts
        items_dict = [item.dict() for item in request.items]
        
        # Create order
        order = await order_logic.create_order(
            vendor_id=vendor_id,
            ceo_id=ceo_id,
            buyer_id=request.buyer_id,
            items=items_dict,
            notes=request.notes
        )
        
        return format_response(
            status="success",
            message="Order created successfully",
            data=order
        )
        
    except ValueError as ve:
        logger.warning(f"Order creation validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    authorization: str = Header(None)
):
    """
    Get order details (Vendor or Buyer).
    
    **Authorization**: Vendor or Buyer JWT token required
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Order retrieved successfully",
        "data": {
            "order_id": "ord_1700000000_a1b2c3d4",
            "vendor_id": "vendor_123",
            "buyer_id": "wa_2348012345678",
            "ceo_id": "ceo_456",
            "items": [...],
            "total_amount": 10000.00,
            "currency": "NGN",
            "status": "confirmed",
            "created_at": 1700000000,
            "updated_at": 1700000000
        }
    }
    ```
    """
    try:
        # Try vendor token first, then buyer token
        try:
            payload = verify_vendor_token(authorization)
            role = "Vendor"
        except:
            payload = verify_buyer_token(authorization)
            role = "Buyer"
        
        user_id = payload.get("sub")
        
        # Get order with authorization check
        order = order_logic.get_order_details(
            order_id=order_id,
            user_id=user_id,
            role=role
        )
        
        return format_response(
            status="success",
            message="Order retrieved successfully",
            data=order
        )
        
    except ValueError as ve:
        logger.warning(f"Order retrieval error: {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("")
async def list_orders(
    status: Optional[str] = None,
    authorization: str = Header(None)
):
    """
    List orders for a vendor with optional status filter (Vendor only).
    
    **Authorization**: Vendor JWT token required
    
    **Query Parameters**:
    - `status` (optional): Filter by status (pending/confirmed/paid/completed/cancelled)
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Orders retrieved successfully",
        "data": {
            "orders": [...],
            "count": 5
        }
    }
    ```
    """
    try:
        # Verify vendor token
        vendor_payload = verify_vendor_token(authorization)
        vendor_id = vendor_payload.get("sub")
        ceo_id = vendor_payload.get("ceo_id")
        
        if not vendor_id or not ceo_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing vendor_id or ceo_id")
        
        # List orders
        orders = order_logic.list_orders_for_vendor(
            vendor_id=vendor_id,
            ceo_id=ceo_id,
            status=status
        )
        
        return format_response(
            status="success",
            message="Orders retrieved successfully",
            data={
                "orders": orders,
                "count": len(orders)
            }
        )
        
    except ValueError as ve:
        logger.warning(f"Order listing validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{order_id}/confirm")
async def confirm_order(
    order_id: str,
    request: ConfirmOrderRequest
):
    """
    Confirm an order (Buyer only, called from chatbot).
    
    Changes order status from 'pending' to 'confirmed'.
    
    **Request Body**:
    ```json
    {
        "buyer_id": "wa_2348012345678"
    }
    ```
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Order confirmed successfully",
        "data": {
            "order_id": "ord_1700000000_a1b2c3d4",
            "status": "confirmed",
            "updated_at": 1700000000
        }
    }
    ```
    """
    try:
        # Confirm order
        order = await order_logic.confirm_order(
            order_id=order_id,
            buyer_id=request.buyer_id
        )
        
        return format_response(
            status="success",
            message="Order confirmed successfully",
            data=order
        )
        
    except ValueError as ve:
        logger.warning(f"Order confirmation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Order confirmation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    request: CancelOrderRequest
):
    """
    Cancel an order (Buyer only, called from chatbot).
    
    Changes order status to 'cancelled'.
    
    **Request Body**:
    ```json
    {
        "buyer_id": "wa_2348012345678",
        "reason": "Changed my mind"
    }
    ```
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Order cancelled successfully",
        "data": {
            "order_id": "ord_1700000000_a1b2c3d4",
            "status": "cancelled",
            "updated_at": 1700000000
        }
    }
    ```
    """
    try:
        # Cancel order
        order = await order_logic.cancel_order(
            order_id=order_id,
            buyer_id=request.buyer_id,
            reason=request.reason
        )
        
        return format_response(
            status="success",
            message="Order cancelled successfully",
            data=order
        )
        
    except ValueError as ve:
        logger.warning(f"Order cancellation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Order cancellation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{order_id}/receipt")
async def add_receipt(
    order_id: str,
    request: AddReceiptRequest
):
    """
    Add payment receipt to order (Buyer only, called from chatbot).
    
    Changes order status from 'confirmed' to 'paid'.
    
    **Request Body**:
    ```json
    {
        "buyer_id": "wa_2348012345678",
        "receipt_url": "https://s3.amazonaws.com/trustguard-receipts/.../receipt.jpg"
    }
    ```
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Receipt uploaded successfully",
        "data": {
            "order_id": "ord_1700000000_a1b2c3d4",
            "status": "paid",
            "receipt_url": "https://...",
            "updated_at": 1700000000
        }
    }
    ```
    """
    try:
        # Add receipt to order
        order = await order_logic.add_receipt_to_order(
            order_id=order_id,
            buyer_id=request.buyer_id,
            receipt_url=request.receipt_url
        )
        
        return format_response(
            status="success",
            message="Receipt uploaded successfully",
            data=order
        )
        
    except ValueError as ve:
        logger.warning(f"Receipt upload error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Receipt upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
