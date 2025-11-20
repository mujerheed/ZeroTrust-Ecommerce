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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from common.logger import logger
from .utils import format_response, verify_vendor_token, verify_buyer_token
from . import order_logic
from .pdf_generator import generate_order_pdf


# Pydantic models for request/response validation
class OrderItem(BaseModel):
    """Single order item."""
    name: str = Field(..., description="Item name", min_length=1)
    quantity: int = Field(..., description="Item quantity", gt=0)
    price: float = Field(..., description="Item price per unit", ge=0)
    description: Optional[str] = Field(None, description="Optional item description")


class DeliveryAddress(BaseModel):
    """Delivery address for order."""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    country: str = Field(default="Nigeria", description="Country")
    phone: str = Field(..., description="Contact phone for delivery")
    landmark: Optional[str] = Field(None, description="Nearby landmark for easier location")


class CreateOrderRequest(BaseModel):
    """Request body for creating an order."""
    buyer_id: str = Field(..., description="Buyer identifier (wa_xxx or ig_xxx)")
    items: List[OrderItem] = Field(..., description="Order items", min_items=1)
    notes: Optional[str] = Field(None, description="Optional order notes")
    requires_delivery: bool = Field(default=False, description="Whether buyer wants delivery")
    delivery_address: Optional[DeliveryAddress] = Field(None, description="Custom delivery address (if different from registered address)")
    use_registered_address: bool = Field(default=True, description="Use buyer's registered address for delivery")


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
router = APIRouter(tags=["Orders"])


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
        
        # Prepare delivery address dict if provided
        delivery_address_dict = None
        if request.delivery_address:
            delivery_address_dict = request.delivery_address.dict()
        
        # Create order
        order = await order_logic.create_order(
            vendor_id=vendor_id,
            ceo_id=ceo_id,
            buyer_id=request.buyer_id,
            items=items_dict,
            notes=request.notes,
            requires_delivery=request.requires_delivery,
            delivery_address=delivery_address_dict,
            use_registered_address=request.use_registered_address
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


class UpdateDeliveryRequest(BaseModel):
    """Request body for updating delivery address."""
    buyer_id: str = Field(..., description="Buyer identifier")
    requires_delivery: bool = Field(..., description="Whether buyer wants delivery")
    delivery_address: Optional[DeliveryAddress] = Field(None, description="Delivery address (if requires_delivery=True)")
    use_registered_address: bool = Field(default=False, description="Use buyer's registered address")


@router.patch("/{order_id}/delivery")
async def update_delivery_address(
    order_id: str,
    request: UpdateDeliveryRequest
):
    """
    Update delivery address for an order (Buyer only).
    
    Buyer can:
    1. Enable/disable delivery requirement
    2. Use their registered address (use_registered_address=True)
    3. Provide a custom delivery address (delivery_address)
    
    **Path Parameters**:
    - order_id: Order identifier
    
    **Request Body**:
    ```json
    {
        "buyer_id": "wa_2348012345678",
        "requires_delivery": true,
        "use_registered_address": true
    }
    ```
    
    Or with custom address:
    ```json
    {
        "buyer_id": "wa_2348012345678",
        "requires_delivery": true,
        "use_registered_address": false,
        "delivery_address": {
            "street": "123 Main St",
            "city": "Lagos",
            "state": "Lagos State",
            "country": "Nigeria",
            "phone": "+2348012345678",
            "landmark": "Near City Mall"
        }
    }
    ```
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Delivery address updated",
        "data": {
            "order_id": "ord_1700000000_a1b2c3d4",
            "requires_delivery": true,
            "delivery_address": {...},
            "updated_at": 1700000000
        }
    }
    ```
    """
    try:
        # Validate request
        if request.requires_delivery:
            if not request.use_registered_address and not request.delivery_address:
                raise HTTPException(
                    status_code=400,
                    detail="Either use_registered_address must be True or delivery_address must be provided"
                )
        
        # Convert delivery address to dict if provided
        delivery_addr = request.delivery_address.dict() if request.delivery_address else None
        
        # Update delivery address
        order = await order_logic.update_delivery_address(
            order_id=order_id,
            buyer_id=request.buyer_id,
            requires_delivery=request.requires_delivery,
            delivery_address=delivery_addr,
            use_registered_address=request.use_registered_address
        )
        
        return format_response(
            status="success",
            message="Delivery address updated successfully",
            data=order
        )
        
    except ValueError as ve:
        logger.warning(f"Delivery address update error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Delivery address update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/orders/{order_id}/summary")
async def get_order_summary(
    order_id: str,
    authorization: str = Header(None)
):
    """
    Get comprehensive order summary (for vendor/buyer dashboard or PDF generation).
    
    Returns detailed order information including:
    - Order metadata (ID, status, dates)
    - Items with quantities and prices
    - Payment details (bank account from CEO)
    - Delivery information (if applicable)
    - Receipt information (if uploaded)
    - Totals and currency
    
    **Authorization**: Vendor or Buyer JWT token
    
    **Path Parameters**:
    - `order_id` (str): Order identifier
    
    **Response** (200 OK):
    ```json
    {
        "status": "success",
        "message": "Order summary retrieved",
        "data": {
            "order_id": "ord_123",
            "status": "pending_payment",
            "created_at": 1700000000,
            "updated_at": 1700000000,
            "buyer_id": "wa_1234567890",
            "vendor_id": "vendor_abc",
            "ceo_id": "ceo_xyz",
            "items": [
                {
                    "name": "Product A",
                    "quantity": 2,
                    "price": 5000.00,
                    "subtotal": 10000.00,
                    "description": "Product description"
                }
            ],
            "total_amount": 10000.00,
            "currency": "NGN",
            "payment_details": {
                "bank_name": "First Bank",
                "account_number": "1234567890",
                "account_name": "Business Name",
                "instructions": "Please make payment..."
            },
            "requires_delivery": true,
            "delivery_address": {
                "street": "123 Main St",
                "city": "Lagos",
                "state": "Lagos State",
                "postal_code": "100001",
                "country": "Nigeria",
                "phone": "+2348012345678",
                "landmark": "Near XYZ Mall"
            },
            "receipt": {
                "receipt_id": "rcpt_123",
                "uploaded_at": 1700000100,
                "status": "pending_verification"
            },
            "notes": "Customer notes here"
        }
    }
    ```
    """
    try:
        # Verify token (works for both vendor and buyer)
        token = authorization.replace("Bearer ", "") if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Missing authorization token")
        
        # Try to verify as vendor first, then buyer
        try:
            vendor_data = verify_vendor_token(token)
            user_id = vendor_data["vendor_id"]
            role = "Vendor"
        except:
            buyer_data = verify_buyer_token(token)
            user_id = buyer_data["buyer_id"]
            role = "Buyer"
        
        # Get order summary
        summary = await order_logic.get_order_summary(order_id, user_id, role)
        
        return format_response(
            status="success",
            message="Order summary retrieved successfully",
            data=summary
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"Order summary error: {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Order summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/orders/{order_id}/download-pdf")
async def download_order_pdf(
    order_id: str,
    authorization: str = Header(None)
):
    """
    Download order summary as PDF.
    
    Generates a professional PDF invoice/receipt with:
    - Order details (ID, status, date)
    - Items with quantities, prices, and subtotals
    - Total amount in NGN
    - Payment details (bank account from CEO)
    - Delivery address (if applicable)
    - Receipt status (if uploaded)
    - QR code for order tracking
    
    **Authorization**: Vendor or Buyer JWT token
    
    **Path Parameters**:
    - `order_id` (str): Order identifier
    
    **Response**: PDF file (application/pdf)
    - Content-Disposition: attachment; filename="order_{order_id}.pdf"
    """
    try:
        # Verify token (works for both vendor and buyer)
        token = authorization.replace("Bearer ", "") if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Missing authorization token")
        
        # Try to verify as vendor first, then buyer
        try:
            vendor_data = verify_vendor_token(token)
            user_id = vendor_data["vendor_id"]
            role = "Vendor"
        except:
            buyer_data = verify_buyer_token(token)
            user_id = buyer_data["buyer_id"]
            role = "Buyer"
        
        # Get order summary
        summary = await order_logic.get_order_summary(order_id, user_id, role)
        
        # Generate PDF
        pdf_buffer = generate_order_pdf(summary)
        
        # Return PDF as downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="order_{order_id}.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"PDF generation error: {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
