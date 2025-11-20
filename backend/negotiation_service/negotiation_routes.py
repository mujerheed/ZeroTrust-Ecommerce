"""
FastAPI routes for price negotiation management.

Endpoints:
- POST /negotiations/request-quote - Buyer requests quote (buyer)
- GET /negotiations - List negotiations (buyer/vendor)
- GET /negotiations/{negotiation_id} - Get negotiation details
- POST /negotiations/{negotiation_id}/quote - Vendor provides quote (vendor)
- POST /negotiations/{negotiation_id}/counter - Buyer counter-offer (buyer)
- PATCH /negotiations/{negotiation_id}/accept - Accept negotiation (either)
- PATCH /negotiations/{negotiation_id}/reject - Reject negotiation (either)
- POST /negotiations/{negotiation_id}/convert-to-order - Convert to order (buyer)
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from decimal import Decimal
from common.logger import logger
from order_service.utils import verify_vendor_token, verify_buyer_token, format_response
from . import negotiation_logic


router = APIRouter()


# Pydantic models
class NegotiationItem(BaseModel):
    """Item in negotiation request (no price yet)."""
    name: str = Field(..., description="Item name", min_length=1)
    quantity: int = Field(..., description="Quantity requested", gt=0)
    description: Optional[str] = Field(None, description="Optional item description")


class QuotedItem(BaseModel):
    """Item with vendor pricing."""
    name: str = Field(..., description="Item name", min_length=1)
    quantity: int = Field(..., description="Quantity", gt=0)
    unit_price: float = Field(..., description="Price per unit", ge=0)
    description: Optional[str] = Field(None, description="Optional description")


class DeliveryAddress(BaseModel):
    """Delivery address for negotiation/order."""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    country: str = Field(default="Nigeria", description="Country")
    phone: str = Field(..., description="Contact phone for delivery")


class RequestQuoteRequest(BaseModel):
    """Request body for quote request."""
    vendor_id: str = Field(..., description="Vendor to request quote from")
    items: List[NegotiationItem] = Field(..., description="Items with quantities", min_items=1)
    delivery_address: Optional[DeliveryAddress] = Field(None, description="Delivery address")
    notes: Optional[str] = Field(None, description="Buyer notes/requirements")


class ProvideQuoteRequest(BaseModel):
    """Request body for vendor quote."""
    items: List[QuotedItem] = Field(..., description="Items with pricing", min_items=1)
    notes: Optional[str] = Field(None, description="Vendor notes")


class CounterOfferRequest(BaseModel):
    """Request body for buyer counter-offer."""
    requested_discount: Optional[float] = Field(None, description="Discount % requested", ge=0, le=100)
    counter_total: Optional[float] = Field(None, description="Counter-offer total amount", ge=0)
    notes: Optional[str] = Field(None, description="Buyer's reasoning")


class AcceptNegotiationRequest(BaseModel):
    """Request body for accepting negotiation."""
    final_amount: Optional[float] = Field(None, description="Final agreed amount", ge=0)


class RejectNegotiationRequest(BaseModel):
    """Request body for rejecting negotiation."""
    reason: Optional[str] = Field(None, description="Rejection reason")


# Routes
@router.post("/request-quote")
async def request_quote(
    request: RequestQuoteRequest,
    authorization: str = Header(None)
):
    """
    Buyer requests a price quote from vendor.
    
    Flow:
    1. Buyer specifies items and quantities
    2. Vendor receives notification
    3. Vendor provides pricing
    """
    try:
        # Verify buyer token
        token_payload = verify_buyer_token(authorization)
        buyer_id = token_payload["sub"]
        ceo_id = token_payload.get("ceo_id")
        
        if not ceo_id:
            raise HTTPException(status_code=400, detail="CEO ID missing in token")
        
        # Convert to dict for logic layer
        items = [item.dict() for item in request.items]
        delivery_addr = request.delivery_address.dict() if request.delivery_address else None
        
        # Create negotiation
        negotiation = await negotiation_logic.request_quote(
            buyer_id=buyer_id,
            vendor_id=request.vendor_id,
            ceo_id=ceo_id,
            items=items,
            delivery_address=delivery_addr,
            notes=request.notes
        )
        
        return format_response(
            "success",
            "Quote request sent to vendor",
            negotiation
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Request quote failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to request quote")


@router.get("")
async def list_negotiations(
    status: Optional[str] = None,
    authorization: str = Header(None)
):
    """
    List negotiations for authenticated user (buyer or vendor).
    
    Query params:
    - status: Filter by status (pending_quote, quoted, counter_offer, accepted, rejected)
    """
    try:
        # Try to verify as buyer first
        try:
            token_payload = verify_buyer_token(authorization)
            user_id = token_payload["sub"]
            role = "buyer"
        except:
            # Try as vendor
            token_payload = verify_vendor_token(authorization)
            user_id = token_payload["sub"]
            role = "vendor"
        
        # List negotiations
        if role == "buyer":
            from .database import list_negotiations_by_buyer
            negotiations = list_negotiations_by_buyer(user_id, status)
        else:
            from .database import list_negotiations_by_vendor
            negotiations = list_negotiations_by_vendor(user_id, status)
        
        return format_response(
            "success",
            f"Retrieved {len(negotiations)} negotiations",
            {"negotiations": negotiations, "count": len(negotiations)}
        )
        
    except Exception as e:
        logger.error(f"List negotiations failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list negotiations")


@router.get("/{negotiation_id}")
async def get_negotiation(
    negotiation_id: str,
    authorization: str = Header(None)
):
    """
    Get negotiation details.
    
    Authorization: Buyer or vendor involved in the negotiation
    """
    try:
        # Verify token (buyer or vendor)
        try:
            token_payload = verify_buyer_token(authorization)
        except:
            token_payload = verify_vendor_token(authorization)
        
        user_id = token_payload["sub"]
        
        # Get negotiation
        from .database import get_negotiation as db_get_negotiation
        negotiation = db_get_negotiation(negotiation_id)
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        # Verify authorization
        if user_id not in [negotiation.get("buyer_id"), negotiation.get("vendor_id")]:
            raise HTTPException(status_code=403, detail="Not authorized for this negotiation")
        
        return format_response(
            "success",
            "Negotiation retrieved",
            negotiation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get negotiation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve negotiation")


@router.post("/{negotiation_id}/quote")
async def provide_quote(
    negotiation_id: str,
    request: ProvideQuoteRequest,
    authorization: str = Header(None)
):
    """
    Vendor provides pricing quote.
    
    Authorization: Vendor only
    """
    try:
        # Verify vendor token
        token_payload = verify_vendor_token(authorization)
        vendor_id = token_payload["sub"]
        
        # Convert to dict
        quoted_items = [item.dict() for item in request.items]
        
        # Provide quote
        negotiation = await negotiation_logic.vendor_provide_quote(
            negotiation_id=negotiation_id,
            vendor_id=vendor_id,
            quoted_items=quoted_items,
            notes=request.notes
        )
        
        return format_response(
            "success",
            "Quote provided successfully",
            negotiation
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Provide quote failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to provide quote")


@router.post("/{negotiation_id}/counter")
async def counter_offer(
    negotiation_id: str,
    request: CounterOfferRequest,
    authorization: str = Header(None)
):
    """
    Buyer submits counter-offer or requests discount.
    
    Authorization: Buyer only
    """
    try:
        # Verify buyer token
        token_payload = verify_buyer_token(authorization)
        buyer_id = token_payload["sub"]
        
        # Submit counter
        negotiation = await negotiation_logic.buyer_counter_offer(
            negotiation_id=negotiation_id,
            buyer_id=buyer_id,
            requested_discount=request.requested_discount,
            counter_total=request.counter_total,
            notes=request.notes
        )
        
        return format_response(
            "success",
            "Counter-offer submitted",
            negotiation
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Counter-offer failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit counter-offer")


@router.patch("/{negotiation_id}/accept")
async def accept_negotiation(
    negotiation_id: str,
    request: AcceptNegotiationRequest,
    authorization: str = Header(None)
):
    """
    Accept the negotiation (buyer or vendor).
    
    Authorization: Buyer or vendor involved
    """
    try:
        # Verify token (buyer or vendor)
        try:
            token_payload = verify_buyer_token(authorization)
        except:
            token_payload = verify_vendor_token(authorization)
        
        user_id = token_payload["sub"]
        
        # Accept negotiation
        negotiation = await negotiation_logic.accept_negotiation(
            negotiation_id=negotiation_id,
            user_id=user_id,
            final_amount=request.final_amount
        )
        
        return format_response(
            "success",
            "Negotiation accepted! Ready to convert to order.",
            negotiation
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Accept negotiation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to accept negotiation")


@router.patch("/{negotiation_id}/reject")
async def reject_negotiation(
    negotiation_id: str,
    request: RejectNegotiationRequest,
    authorization: str = Header(None)
):
    """
    Reject the negotiation (buyer or vendor).
    
    Authorization: Buyer or vendor involved
    """
    try:
        # Verify token (buyer or vendor)
        try:
            token_payload = verify_buyer_token(authorization)
        except:
            token_payload = verify_vendor_token(authorization)
        
        user_id = token_payload["sub"]
        
        # Reject negotiation
        negotiation = await negotiation_logic.reject_negotiation(
            negotiation_id=negotiation_id,
            user_id=user_id,
            reason=request.reason
        )
        
        return format_response(
            "success",
            "Negotiation rejected",
            negotiation
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Reject negotiation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject negotiation")


@router.post("/{negotiation_id}/convert-to-order")
async def convert_to_order(
    negotiation_id: str,
    authorization: str = Header(None)
):
    """
    Convert accepted negotiation to actual order.
    
    Authorization: Buyer only
    Status: Must be "accepted"
    """
    try:
        # Verify buyer token
        token_payload = verify_buyer_token(authorization)
        buyer_id = token_payload["sub"]
        ceo_id = token_payload.get("ceo_id")
        
        # Get negotiation
        from .database import get_negotiation as db_get_negotiation
        negotiation = db_get_negotiation(negotiation_id)
        
        if not negotiation:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        # Verify buyer
        if negotiation.get("buyer_id") != buyer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify status
        if negotiation.get("status") != "accepted":
            raise HTTPException(status_code=400, detail="Negotiation must be accepted first")
        
        # Convert to order
        from order_service import order_logic
        
        # Prepare order data from negotiation
        items = []
        for item in negotiation.get("vendor_quote", []):
            items.append({
                "name": item.get("name"),
                "quantity": float(item.get("quantity", 0)),
                "price": float(item.get("unit_price", 0)),
                "description": item.get("description")
            })
        
        # Create order
        order = await order_logic.create_order(
            vendor_id=negotiation["vendor_id"],
            buyer_id=buyer_id,
            ceo_id=ceo_id,
            items=items,
            notes=f"Converted from negotiation {negotiation_id}. Final amount: ₦{negotiation.get('final_amount')}"
        )
        
        # Mark negotiation as converted
        from .database import update_negotiation_status
        update_negotiation_status(
            negotiation_id=negotiation_id,
            status="converted_to_order"
        )
        
        return format_response(
            "success",
            "Negotiation converted to order",
            {
                "order": order,
                "negotiation_id": negotiation_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Convert to order failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to convert to order")
