# backend/auth_service/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

client = TestClient(app)

@pytest.fixture
def mock_db_functions():
    with patch("auth_service.auth_logic.create_ceo") as mock_create_ceo, \
         patch("auth_service.auth_logic.get_user_by_email") as mock_get_email, \
         patch("auth_service.auth_logic.get_user_by_phone") as mock_get_phone, \
         patch("auth_service.auth_logic.request_otp") as mock_request_otp:
        yield {
            "create_ceo": mock_create_ceo,
            "get_user_by_email": mock_get_email,
            "get_user_by_phone": mock_get_phone,
            "request_otp": mock_request_otp
        }

def test_register_ceo_success(mock_db_functions):
    """Test successful CEO registration."""
    mock_db_functions["request_otp"].return_value = {"delivery_method": "email"}
    
    payload = {
        "name": "John CEO",
        "phone": "+2348012345678",
        "email": "ceo@example.com"
    }
    
    response = client.post("/auth/ceo/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "ceo_id" in data["data"]
    
    # Verify DB call
    mock_db_functions["create_ceo"].assert_called_once()

def test_register_ceo_invalid_phone(mock_db_functions):
    """Test registration with invalid phone format."""
    payload = {
        "name": "John CEO",
        "phone": "12345", # Invalid
        "email": "ceo@example.com"
    }
    
    response = client.post("/auth/ceo/register", json=payload)
    assert response.status_code == 400

def test_login_ceo_success(mock_db_functions):
    """Test CEO login sends OTP."""
    # Mock user found
    mock_db_functions["get_user_by_email"].return_value = {
        "user_id": "ceo_123",
        "status": "active",
        "phone": "+2348012345678"
    }
    mock_db_functions["request_otp"].return_value = {"delivery_method": "email"}
    
    payload = {"contact": "ceo@example.com"}
    response = client.post("/auth/ceo/login", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["ceo_id"] == "ceo_123"

def test_login_ceo_not_found(mock_db_functions):
    """Test login with unknown user."""
    mock_db_functions["get_user_by_email"].return_value = None
    
    payload = {"contact": "unknown@example.com"}
    response = client.post("/auth/ceo/login", json=payload)
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
