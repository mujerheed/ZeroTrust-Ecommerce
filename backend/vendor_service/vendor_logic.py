"""
Core business logic for vendor operations.
"""

from .database import get_order, save_receipt
from .transaction_manager import create_order, verify_order_payment

def place_order(vendor_id: str, order_id: str, amount: float):
    """
    Vendor creates a new order.
    """
    return create_order(order_id, vendor_id, amount)

def upload_receipt(vendor_id: str, order_id: str, receipt_url: str):
    """
    Vendor uploads a proof-of-payment receipt.
    """
    # Persist receipt link
    save_receipt(order_id, receipt_url)
    return {"order_id": order_id, "receipt_url": receipt_url}

def confirm_payment(order_id: str, otp: str):
    """
    Vendor confirms payment using OTP.
    """
    return verify_order_payment(order_id, otp)
