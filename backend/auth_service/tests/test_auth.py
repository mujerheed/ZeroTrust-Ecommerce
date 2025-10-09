# backend/auth_service/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from auth_service.auth_routes import router as auth_router
from auth_service.auth_logic import _users_db
from auth_service.otp_manager import _otp_store
from backend.app import app  # assuming app.py exposes FastAPI app

# Mount auth router on test app
app.include_router(auth_router, prefix="/auth")
client = TestClient(app)


def setup_function():
    """Clear in-memory stores before each test."""
    _users_db.clear()
    _otp_store.clear()


def test_register_user_success():
    """Test successful user registration."""
    payload = {"email": "user@example.com", "phone": "08012345678", "name": "John Doe"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert "user_id" in data


def test_register_user_invalid_email():
    """Test registration with invalid email format."""
    payload = {"email": "invalid-email", "phone": "08012345678", "name": "John Doe"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_login_user_success(monkeypatch):
    """Test login endpoint sends OTP successfully."""
    # First register a user
    reg_resp = client.post("/auth/register", json={
        "email": "user2@example.com", "phone": "08012345679", "name": "Jane Doe"
    })
    user_id = reg_resp.json()["user_id"]
    
    # Stub send_otp to avoid real SMS
    monkeypatch.setattr("auth_service.otp_manager.send_otp", lambda phone, otp: None)
    
    response = client.post("/auth/login", json={"user_id": user_id})
    assert response.status_code == 200
    assert response.json()["message"] == "OTP sent"
    # OTP store should have an entry
    assert user_id in _otp_store


def test_login_user_not_found():
    """Test login with non-existent user returns error."""
    response = client.post("/auth/login", json={"user_id": "nonexistent"})
    assert response.status_code == 400


def test_verify_otp_success(monkeypatch):
    """Test OTP verification success."""
    # Prepare OTP store
    user_id = "user-1"
    _otp_store[user_id] = ("ABC123!@", __import__("datetime").datetime.utcnow())
    
    response = client.post("/auth/verify-otp", json={"user_id": user_id, "otp": "ABC123!@"})
    assert response.status_code == 200
    assert response.json()["message"] == "OTP verified successfully"
    # OTP should be removed after successful verification
    assert user_id not in _otp_store


def test_verify_otp_invalid():
    """Test OTP verification with wrong code."""
    user_id = "user-2"
    _otp_store[user_id] = ("XYZ789!@", __import__("datetime").datetime.utcnow())
    
    response = client.post("/auth/verify-otp", json={"user_id": user_id, "otp": "WRONG"})
    assert response.status_code == 401
