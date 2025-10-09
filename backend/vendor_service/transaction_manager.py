"""
Handles transaction workflows, including OTP validation integration.
"""

from auth_service.otp_manager import validate_otp
from database import get_order, save_order

def create_order(order_id: str, vendor_id: str, amount: float):
    """
    Create a new order record.
    """
    order = {
        "order_id": order_id,
        "vendor_id": vendor_id,
        "amount": amount,
        "status": "pending",
        "created_at": __import__("datetime").datetime.utcnow().isoformat()
    }
    save_order(order_id, order)
    return order

def verify_order_payment(order_id: str, otp: str):
    """
    Validate OTP for payment confirmation, update order status.
    """
    order = get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    # Validate OTP via auth service
    if not validate_otp(order["vendor_id"], otp):
        raise ValueError("Invalid or expired OTP")
    order["status"] = "paid"
    save_order(order_id, order)
    return order
