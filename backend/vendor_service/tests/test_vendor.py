import pytest
from vendor_service.vendor_logic import place_order, upload_receipt, confirm_payment
from vendor_service.database import _orders, _receipts

def test_place_order():
    order = place_order("vendor1", "order-1", 100.0)
    assert order["status"] == "pending"
    assert _orders["order-1"]["amount"] == 100.0

def test_upload_receipt():
    upload_receipt("vendor1", "order-1", "https://example.com/receipt.png")
    assert _receipts["order-1"] == "https://example.com/receipt.png"

def test_confirm_payment_invalid_otp(monkeypatch):
    # Simulate invalid OTP
    def fake_validate(user_id, otp): return False
    monkeypatch.setattr("vendor_service.transaction_manager.validate_otp", fake_validate)
    with pytest.raises(ValueError):
        confirm_payment("order-1", "wrongotp")

def test_confirm_payment_valid_otp(monkeypatch):
    # Reset order for test
    place_order("vendor1", "order-2", 50.0)
    def fake_validate(user_id, otp): return True
    monkeypatch.setattr("vendor_service.transaction_manager.validate_otp", fake_validate)
    order = confirm_payment("order-2", "correctotp")
    assert order["status"] == "paid"
