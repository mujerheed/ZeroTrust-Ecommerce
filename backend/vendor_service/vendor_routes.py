from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from .vendor_logic import place_order, upload_receipt, confirm_payment
from .utils import format_response, validate_order_id

router = APIRouter()

class OrderRequest(BaseModel):
    vendor_id: str
    order_id: str
    amount: float

@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order_route(req: OrderRequest):
    try:
        validate_order_id(req.order_id)
        order = place_order(req.vendor_id, req.order_id, req.amount)
        return format_response("success", "Order placed", order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ReceiptRequest(BaseModel):
    vendor_id: str
    order_id: str
    receipt_url: str

@router.post("/orders/receipt")
async def upload_receipt_route(req: ReceiptRequest):
    try:
        validate_order_id(req.order_id)
        result = upload_receipt(req.vendor_id, req.order_id, req.receipt_url)
        return format_response("success", "Receipt uploaded", result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ConfirmPaymentRequest(BaseModel):
    order_id: str
    otp: str

@router.post("/orders/confirm")
async def confirm_payment_route(req: ConfirmPaymentRequest):
    try:
        validate_order_id(req.order_id)
        order = confirm_payment(req.order_id, req.otp)
        return format_response("success", "Payment confirmed", order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
