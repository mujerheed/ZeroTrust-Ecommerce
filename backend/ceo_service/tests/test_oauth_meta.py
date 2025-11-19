"""
Tests for OAuth Meta Connection (WhatsApp & Instagram)

Tests cover:
1. State token generation and validation
2. Authorization URL generation
3. OAuth callback handling (mocked)
4. Token storage and retrieval from Secrets Manager
5. Connection status checking
6. Token revocation

Run with: pytest ceo_service/tests/test_oauth_meta.py
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from ceo_service import oauth_meta
from ceo_service.oauth_meta import (
    generate_state_token,
    validate_state_token,
    get_authorization_url,
    exchange_code_for_token,
    store_token_in_secrets_manager,
    get_token_from_secrets_manager,
    revoke_connection,
    get_connection_status,
    handle_oauth_callback
)


# ==================== Test Fixtures ====================

@pytest.fixture
def mock_ceo_id():
    return "ceo_test_12345"


@pytest.fixture
def mock_platform():
    return "whatsapp"


@pytest.fixture
def mock_redirect_uri():
    return "http://localhost:8000/ceo/oauth/meta/callback"


@pytest.fixture
def mock_token_response():
    return {
        "access_token": "EAAC123...test_token",
        "token_type": "bearer",
        "expires_in": 5184000  # 60 days
    }


@pytest.fixture
def mock_long_lived_token():
    return {
        "access_token": "EAAC_LONG_LIVED_TOKEN",
        "token_type": "bearer",
        "expires_in": 5184000
    }


@pytest.fixture(autouse=True)
def clear_state_tokens():
    """Clear state tokens before each test."""
    oauth_meta._state_tokens.clear()
    yield
    oauth_meta._state_tokens.clear()


# ==================== State Token Tests ====================

def test_generate_state_token(mock_ceo_id, mock_platform):
    """Test state token generation."""
    state_token = generate_state_token(mock_ceo_id, mock_platform)
    
    # Token should be a 64-character hex string
    assert isinstance(state_token, str)
    assert len(state_token) == 64
    
    # Token should be stored in memory
    assert state_token in oauth_meta._state_tokens
    
    # Token metadata should be correct
    token_data = oauth_meta._state_tokens[state_token]
    assert token_data["ceo_id"] == mock_ceo_id
    assert token_data["platform"] == mock_platform
    assert "expires_at" in token_data


def test_validate_state_token_success(mock_ceo_id, mock_platform):
    """Test successful state token validation."""
    state_token = generate_state_token(mock_ceo_id, mock_platform)
    
    # Validate the token
    result = validate_state_token(state_token)
    
    assert result is not None
    assert result["ceo_id"] == mock_ceo_id
    assert result["platform"] == mock_platform
    
    # Token should be removed after validation (single-use)
    assert state_token not in oauth_meta._state_tokens


def test_validate_state_token_not_found():
    """Test validation of non-existent state token."""
    result = validate_state_token("invalid_token_123")
    assert result is None


def test_validate_state_token_expired(mock_ceo_id, mock_platform):
    """Test validation of expired state token."""
    state_token = generate_state_token(mock_ceo_id, mock_platform)
    
    # Manually expire the token
    oauth_meta._state_tokens[state_token]["expires_at"] = time.time() - 1
    
    result = validate_state_token(state_token)
    assert result is None
    assert state_token not in oauth_meta._state_tokens


# ==================== Authorization URL Tests ====================

def test_get_authorization_url_whatsapp(mock_ceo_id, mock_redirect_uri):
    """Test WhatsApp authorization URL generation."""
    with patch.object(oauth_meta.settings, 'META_APP_ID', 'test_app_id'):
        auth_url = get_authorization_url(mock_ceo_id, "whatsapp", mock_redirect_uri)
        
        assert isinstance(auth_url, str)
        assert "facebook.com" in auth_url
        assert "client_id=test_app_id" in auth_url
        assert f"redirect_uri={mock_redirect_uri}" in auth_url
        assert "whatsapp_business_management" in auth_url
        assert "state=" in auth_url


def test_get_authorization_url_instagram(mock_ceo_id, mock_redirect_uri):
    """Test Instagram authorization URL generation."""
    with patch.object(oauth_meta.settings, 'META_APP_ID', 'test_app_id'):
        auth_url = get_authorization_url(mock_ceo_id, "instagram", mock_redirect_uri)
        
        assert isinstance(auth_url, str)
        assert "instagram_basic" in auth_url or "facebook.com" in auth_url


def test_get_authorization_url_invalid_platform(mock_ceo_id, mock_redirect_uri):
    """Test authorization URL with invalid platform."""
    with pytest.raises(ValueError, match="Invalid platform"):
        get_authorization_url(mock_ceo_id, "tiktok", mock_redirect_uri)


# ==================== Token Exchange Tests ====================

@patch('ceo_service.oauth_meta.requests.get')
def test_exchange_code_for_token_success(mock_get, mock_redirect_uri, mock_token_response):
    """Test successful code-for-token exchange."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.json.return_value = mock_token_response
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    with patch.object(oauth_meta.settings, 'META_APP_ID', 'test_app_id'), \
         patch.object(oauth_meta.settings, 'META_APP_SECRET', 'test_secret'):
        
        result = exchange_code_for_token("test_auth_code", mock_redirect_uri)
        
        assert result["access_token"] == mock_token_response["access_token"]
        assert result["token_type"] == mock_token_response["token_type"]
        assert result["expires_in"] == mock_token_response["expires_in"]


@patch('ceo_service.oauth_meta.requests.get')
def test_exchange_code_for_token_failure(mock_get, mock_redirect_uri):
    """Test failed code-for-token exchange."""
    # Mock failed API response
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("API Error")
    mock_get.return_value = mock_response
    
    with patch.object(oauth_meta.settings, 'META_APP_ID', 'test_app_id'), \
         patch.object(oauth_meta.settings, 'META_APP_SECRET', 'test_secret'):
        
        with pytest.raises(Exception):
            exchange_code_for_token("invalid_code", mock_redirect_uri)


# ==================== Secrets Manager Tests ====================

@patch('ceo_service.oauth_meta.boto3.client')
def test_store_token_in_secrets_manager_new(mock_boto_client, mock_ceo_id, mock_platform, mock_token_response):
    """Test storing new token in Secrets Manager."""
    # Mock Secrets Manager client
    mock_sm_client = MagicMock()
    mock_sm_client.put_secret_value.side_effect = mock_sm_client.exceptions.ResourceNotFoundException()
    mock_sm_client.create_secret.return_value = {"ARN": "arn:aws:secretsmanager:us-east-1:123:secret:test"}
    mock_boto_client.return_value = mock_sm_client
    
    with patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        result = store_token_in_secrets_manager(mock_ceo_id, mock_platform, mock_token_response)
        
        assert result is True or isinstance(result, str)
        mock_sm_client.create_secret.assert_called_once()


@patch('ceo_service.oauth_meta.boto3.client')
def test_store_token_in_secrets_manager_update(mock_boto_client, mock_ceo_id, mock_platform, mock_token_response):
    """Test updating existing token in Secrets Manager."""
    # Mock Secrets Manager client
    mock_sm_client = MagicMock()
    mock_sm_client.put_secret_value.return_value = {"ARN": "arn:aws:secretsmanager:us-east-1:123:secret:test"}
    mock_boto_client.return_value = mock_sm_client
    
    with patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        result = store_token_in_secrets_manager(mock_ceo_id, mock_platform, mock_token_response)
        
        assert result is True or isinstance(result, str)


@patch('ceo_service.oauth_meta.boto3.client')
def test_get_token_from_secrets_manager_success(mock_boto_client, mock_ceo_id, mock_platform):
    """Test retrieving token from Secrets Manager."""
    # Mock Secrets Manager client
    mock_sm_client = MagicMock()
    secret_data = {
        "access_token": "EAAC_TEST_TOKEN",
        "platform": mock_platform,
        "ceo_id": mock_ceo_id,
        "expires_at": time.time() + 86400  # Not expired
    }
    mock_sm_client.get_secret_value.return_value = {
        "SecretString": json.dumps(secret_data)
    }
    mock_boto_client.return_value = mock_sm_client
    
    with patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        result = get_token_from_secrets_manager(mock_ceo_id, mock_platform)
        
        assert result is not None
        assert result["access_token"] == secret_data["access_token"]
        assert result["platform"] == mock_platform


@patch('ceo_service.oauth_meta.boto3.client')
def test_get_token_from_secrets_manager_not_found(mock_boto_client, mock_ceo_id, mock_platform):
    """Test retrieving non-existent token."""
    # Mock Secrets Manager client
    mock_sm_client = MagicMock()
    mock_sm_client.get_secret_value.side_effect = mock_sm_client.exceptions.ResourceNotFoundException({}, "NotFound")
    mock_boto_client.return_value = mock_sm_client
    
    with patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        result = get_token_from_secrets_manager(mock_ceo_id, mock_platform)
        
        assert result is None


@patch('ceo_service.oauth_meta.boto3.client')
def test_get_token_from_secrets_manager_expired(mock_boto_client, mock_ceo_id, mock_platform):
    """Test retrieving expired token."""
    # Mock Secrets Manager client
    mock_sm_client = MagicMock()
    secret_data = {
        "access_token": "EAAC_TEST_TOKEN",
        "platform": mock_platform,
        "ceo_id": mock_ceo_id,
        "expires_at": time.time() - 1  # Expired
    }
    mock_sm_client.get_secret_value.return_value = {
        "SecretString": json.dumps(secret_data)
    }
    mock_boto_client.return_value = mock_sm_client
    
    with patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        result = get_token_from_secrets_manager(mock_ceo_id, mock_platform)
        
        assert result is None


# ==================== Connection Status Tests ====================

@patch('ceo_service.oauth_meta.get_token_from_secrets_manager')
def test_get_connection_status_connected(mock_get_token, mock_ceo_id, mock_platform):
    """Test connection status when connected."""
    mock_get_token.return_value = {
        "access_token": "EAAC_TEST",
        "expires_at": time.time() + (7 * 86400),  # 7 days from now
        "stored_at": time.time() - 86400
    }
    
    result = get_connection_status(mock_ceo_id, mock_platform)
    
    assert result["connected"] is True
    assert result["platform"] == mock_platform
    assert "expires_at" in result
    assert "days_until_expiry" in result


@patch('ceo_service.oauth_meta.get_token_from_secrets_manager')
def test_get_connection_status_not_connected(mock_get_token, mock_ceo_id, mock_platform):
    """Test connection status when not connected."""
    mock_get_token.return_value = None
    
    result = get_connection_status(mock_ceo_id, mock_platform)
    
    assert result["connected"] is False
    assert result["platform"] == mock_platform
    assert "message" in result


# ==================== Revocation Tests ====================

@patch('ceo_service.oauth_meta.boto3.client')
@patch('ceo_service.oauth_meta.get_ceo_by_id')
@patch('ceo_service.oauth_meta.update_ceo')
def test_revoke_connection_success(mock_update_ceo, mock_get_ceo, mock_boto_client, mock_ceo_id, mock_platform):
    """Test successful connection revocation."""
    # Mock CEO record
    mock_get_ceo.return_value = {
        "ceo_id": mock_ceo_id,
        "meta_connections": {
            mock_platform: {"connected": True}
        }
    }
    
    # Mock Secrets Manager client
    mock_sm_client = MagicMock()
    mock_sm_client.delete_secret.return_value = {"ARN": "arn:aws:secretsmanager:..."}
    mock_boto_client.return_value = mock_sm_client
    
    with patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        result = revoke_connection(mock_ceo_id, mock_platform)
        
        assert result is True
        mock_sm_client.delete_secret.assert_called_once()


# ==================== Integration Tests ====================

@patch('ceo_service.oauth_meta.requests.get')
@patch('ceo_service.oauth_meta.store_token_in_secrets_manager')
@patch('ceo_service.oauth_meta.get_ceo_by_id')
@patch('ceo_service.oauth_meta.update_ceo')
def test_handle_oauth_callback_success(
    mock_update_ceo,
    mock_get_ceo,
    mock_store_token,
    mock_requests_get,
    mock_ceo_id,
    mock_platform,
    mock_redirect_uri,
    mock_token_response,
    mock_long_lived_token
):
    """Test successful OAuth callback handling."""
    # Generate valid state token
    state_token = generate_state_token(mock_ceo_id, mock_platform)
    
    # Mock CEO record
    mock_get_ceo.return_value = {
        "ceo_id": mock_ceo_id,
        "meta_connections": {}
    }
    
    # Mock token exchange (short-lived)
    mock_response_short = Mock()
    mock_response_short.json.return_value = mock_token_response
    mock_response_short.raise_for_status = Mock()
    
    # Mock long-lived token exchange
    mock_response_long = Mock()
    mock_response_long.json.return_value = mock_long_lived_token
    mock_response_long.raise_for_status = Mock()
    
    mock_requests_get.side_effect = [mock_response_short, mock_response_long]
    
    # Mock token storage
    mock_store_token.return_value = True
    
    with patch.object(oauth_meta.settings, 'META_APP_ID', 'test_app_id'), \
         patch.object(oauth_meta.settings, 'META_APP_SECRET', 'test_secret'), \
         patch.object(oauth_meta.settings, 'AWS_REGION', 'us-east-1'):
        
        result = handle_oauth_callback("test_code", state_token, mock_redirect_uri)
        
        assert result["success"] is True
        assert result["platform"] == mock_platform
        assert result["ceo_id"] == mock_ceo_id


# ==================== Manual Testing Guide ====================

"""
MANUAL TESTING STEPS FOR REAL META OAUTH:

1. Setup Meta App:
   - Go to https://developers.facebook.com/
   - Create a new app or use existing
   - Enable WhatsApp Business API and/or Instagram Messaging API
   - Get App ID and App Secret
   - Configure OAuth redirect URI: http://localhost:8000/ceo/oauth/meta/callback

2. Update .env file:
   META_APP_ID=<your_app_id>
   META_APP_SECRET=<your_app_secret>
   OAUTH_CALLBACK_BASE_URL=http://localhost:8000

3. Start server:
   cd backend
   source venv/bin/activate
   uvicorn app:app --reload --port 8000

4. Test WhatsApp OAuth:
   - Login as CEO: POST /ceo/login
   - Get JWT token
   - Visit: GET /ceo/oauth/meta/authorize?platform=whatsapp
     (with Authorization: Bearer <token>)
   - Follow Meta OAuth flow in browser
   - Should redirect back to callback URL with code
   - Check connection: GET /ceo/oauth/meta/status?platform=whatsapp

5. Test Instagram OAuth:
   - Same as above but with platform=instagram

6. Test Revocation:
   - POST /ceo/oauth/meta/revoke?platform=whatsapp

7. Verify Secrets Manager:
   - AWS Console > Secrets Manager
   - Check for: TrustGuard/<ceo_id>/meta/whatsapp
   - Verify token is stored

EXPECTED RESULTS:
✅ Authorization URL redirects to Meta
✅ Callback receives code and state
✅ Token stored in Secrets Manager
✅ Connection status shows "connected"
✅ Revocation removes token
"""
