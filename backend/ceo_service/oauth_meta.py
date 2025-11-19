"""
OAuth Meta Connection Logic

Handles WhatsApp Business API and Instagram Messaging API OAuth flows:
- Authorization URL generation
- Callback handling (exchange code for token)
- Token storage in AWS Secrets Manager
- Token refresh logic
- Connection status management
"""

import os
import secrets
import json
import time
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from common.logger import logger
from common.config import settings
from ceo_service.database import get_ceo_by_id, update_ceo


# Meta OAuth Configuration
META_OAUTH_BASE_URL = "https://www.facebook.com/v18.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
META_TOKEN_EXCHANGE_URL = "https://graph.facebook.com/v18.0/oauth/access_token"

# OAuth scopes
WHATSAPP_SCOPES = [
    "whatsapp_business_management",
    "whatsapp_business_messaging",
    "business_management"
]

INSTAGRAM_SCOPES = [
    "instagram_basic",
    "instagram_manage_messages",
    "pages_messaging",
    "pages_show_list"
]

# State token TTL (5 minutes)
STATE_TOKEN_TTL = 300

# In-memory state token storage (production should use Redis/DynamoDB)
_state_tokens: Dict[str, Dict[str, Any]] = {}


# ==================== State Token Management ====================

def generate_state_token(ceo_id: str, platform: str) -> str:
    """
    Generate CSRF protection state token.
    
    Args:
        ceo_id: CEO identifier
        platform: 'whatsapp' or 'instagram'
    
    Returns:
        Secure random state token
    """
    state = secrets.token_urlsafe(32)
    _state_tokens[state] = {
        "ceo_id": ceo_id,
        "platform": platform,
        "created_at": int(time.time()),
        "expires_at": int(time.time()) + STATE_TOKEN_TTL
    }
    
    logger.info("OAuth state token generated", extra={
        "ceo_id": ceo_id,
        "platform": platform,
        "ttl_seconds": STATE_TOKEN_TTL
    })
    
    return state


def validate_state_token(state: str) -> Optional[Dict[str, Any]]:
    """
    Validate OAuth state token and return associated data.
    
    Args:
        state: State token from OAuth callback
    
    Returns:
        Token data if valid, None otherwise
    """
    token_data = _state_tokens.get(state)
    
    if not token_data:
        logger.warning("OAuth state token not found", extra={"state": state[:8] + "..."})
        return None
    
    # Check expiry
    if int(time.time()) > token_data["expires_at"]:
        logger.warning("OAuth state token expired", extra={
            "state": state[:8] + "...",
            "ceo_id": token_data.get("ceo_id")
        })
        _state_tokens.pop(state, None)
        return None
    
    # Remove token after validation (single-use)
    _state_tokens.pop(state, None)
    
    logger.info("OAuth state token validated", extra={
        "ceo_id": token_data.get("ceo_id"),
        "platform": token_data.get("platform")
    })
    
    return token_data


# ==================== OAuth Authorization ====================

def get_authorization_url(ceo_id: str, platform: str, redirect_uri: str) -> str:
    """
    Generate Meta OAuth authorization URL.
    
    Args:
        ceo_id: CEO identifier
        platform: 'whatsapp' or 'instagram'
        redirect_uri: OAuth callback URL
    
    Returns:
        OAuth authorization URL
    
    Raises:
        ValueError: If platform invalid or Meta App ID not configured
    """
    # Validate platform
    if platform not in ["whatsapp", "instagram"]:
        raise ValueError(f"Invalid platform: {platform}. Must be 'whatsapp' or 'instagram'")
    
    # Get Meta App ID from environment
    app_id = os.getenv("META_APP_ID")
    if not app_id:
        raise ValueError("META_APP_ID not configured in environment")
    
    # Select scopes based on platform
    scopes = WHATSAPP_SCOPES if platform == "whatsapp" else INSTAGRAM_SCOPES
    
    # Generate state token for CSRF protection
    state = generate_state_token(ceo_id, platform)
    
    # Build authorization URL
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": ",".join(scopes),
        "response_type": "code",
        "state": state
    }
    
    url = f"{META_OAUTH_BASE_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    logger.info("OAuth authorization URL generated", extra={
        "ceo_id": ceo_id,
        "platform": platform,
        "scopes": scopes
    })
    
    return url


# ==================== Token Exchange ====================

def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange OAuth authorization code for access token.
    
    Args:
        code: Authorization code from Meta callback
        redirect_uri: OAuth callback URL (must match authorization request)
    
    Returns:
        Token response with access_token, token_type, expires_in
    
    Raises:
        ValueError: If token exchange fails
    """
    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Meta App credentials not configured")
    
    # Exchange code for token
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code
    }
    
    try:
        response = requests.get(META_TOKEN_URL, params=params, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        
        logger.info("OAuth token exchange successful", extra={
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in")
        })
        
        return token_data
    
    except requests.RequestException as e:
        logger.error("OAuth token exchange failed", extra={
            "error": str(e),
            "status_code": getattr(e.response, "status_code", None)
        })
        raise ValueError(f"Failed to exchange code for token: {str(e)}")


def exchange_short_for_long_lived_token(short_lived_token: str) -> Dict[str, Any]:
    """
    Exchange short-lived token for long-lived token (60 days).
    
    Args:
        short_lived_token: Short-lived access token from code exchange
    
    Returns:
        Long-lived token data
    
    Raises:
        ValueError: If exchange fails
    """
    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Meta App credentials not configured")
    
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token
    }
    
    try:
        response = requests.get(META_TOKEN_EXCHANGE_URL, params=params, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        
        logger.info("Long-lived token obtained", extra={
            "expires_in": token_data.get("expires_in", 5184000)  # Default 60 days
        })
        
        return token_data
    
    except requests.RequestException as e:
        logger.error("Long-lived token exchange failed", extra={"error": str(e)})
        raise ValueError(f"Failed to get long-lived token: {str(e)}")


# ==================== Token Storage (Secrets Manager) ====================

def store_token_in_secrets_manager(ceo_id: str, platform: str, token_data: Dict[str, Any]) -> bool:
    """
    Store Meta access token in AWS Secrets Manager.
    
    Secret path: /TrustGuard/{ceo_id}/meta/{platform}
    
    Args:
        ceo_id: CEO identifier
        platform: 'whatsapp' or 'instagram'
        token_data: Token response from Meta (access_token, expires_in, etc.)
    
    Returns:
        True if successful
    
    Raises:
        ValueError: If storage fails
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        
        secret_name = f"/TrustGuard/{ceo_id}/meta/{platform}"
        
        # Calculate expiry timestamp
        expires_in = token_data.get("expires_in", 5184000)  # Default 60 days
        expires_at = int(time.time()) + expires_in
        
        secret_value = {
            "access_token": token_data["access_token"],
            "token_type": token_data.get("token_type", "bearer"),
            "expires_in": expires_in,
            "expires_at": expires_at,
            "platform": platform,
            "stored_at": int(time.time()),
            "ceo_id": ceo_id
        }
        
        try:
            # Try to update existing secret
            secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            logger.info("Meta token updated in Secrets Manager", extra={
                "ceo_id": ceo_id,
                "platform": platform,
                "secret_name": secret_name
            })
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create new secret
                secrets_client.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps(secret_value),
                    Description=f"Meta {platform.capitalize()} OAuth token for CEO {ceo_id}"
                )
                logger.info("Meta token created in Secrets Manager", extra={
                    "ceo_id": ceo_id,
                    "platform": platform,
                    "secret_name": secret_name
                })
            else:
                raise
        
        return True
    
    except Exception as e:
        logger.error("Failed to store token in Secrets Manager", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise ValueError(f"Token storage failed: {str(e)}")


def get_token_from_secrets_manager(ceo_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve Meta access token from AWS Secrets Manager.
    
    Args:
        ceo_id: CEO identifier
        platform: 'whatsapp' or 'instagram'
    
    Returns:
        Token data if found, None otherwise
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        secret_name = f"/TrustGuard/{ceo_id}/meta/{platform}"
        
        response = secrets_client.get_secret_value(SecretId=secret_name)
        token_data = json.loads(response['SecretString'])
        
        logger.info("Meta token retrieved from Secrets Manager", extra={
            "ceo_id": ceo_id,
            "platform": platform
        })
        
        return token_data
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info("Meta token not found in Secrets Manager", extra={
                "ceo_id": ceo_id,
                "platform": platform
            })
            return None
        else:
            logger.error("Failed to retrieve token from Secrets Manager", extra={
                "ceo_id": ceo_id,
                "platform": platform,
                "error": str(e)
            })
            return None


# ==================== OAuth Callback Handler ====================

def handle_oauth_callback(code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Handle OAuth callback from Meta.
    
    Workflow:
    1. Validate state token
    2. Exchange code for short-lived token
    3. Exchange for long-lived token (60 days)
    4. Store in Secrets Manager
    5. Update CEO record with connection status
    
    Args:
        code: Authorization code from Meta
        state: State token for CSRF protection
        redirect_uri: OAuth callback URL
    
    Returns:
        Connection status data
    
    Raises:
        ValueError: If callback handling fails
    """
    # Step 1: Validate state token
    token_data = validate_state_token(state)
    if not token_data:
        raise ValueError("Invalid or expired state token")
    
    ceo_id = token_data["ceo_id"]
    platform = token_data["platform"]
    
    try:
        # Step 2: Exchange code for short-lived token
        short_token_response = exchange_code_for_token(code, redirect_uri)
        short_lived_token = short_token_response["access_token"]
        
        # Step 3: Exchange for long-lived token
        long_token_response = exchange_short_for_long_lived_token(short_lived_token)
        
        # Step 4: Store in Secrets Manager
        store_token_in_secrets_manager(ceo_id, platform, long_token_response)
        
        # Step 5: Update CEO record
        connection_data = {
            f"{platform}_connected": True,
            f"{platform}_connected_at": int(time.time()),
            f"{platform}_token_expires_at": int(time.time()) + long_token_response.get("expires_in", 5184000)
        }
        
        # Update CEO meta_connections field
        ceo = get_ceo_by_id(ceo_id)
        meta_connections = ceo.get("meta_connections", {})
        meta_connections[platform] = {
            "connected": True,
            "connected_at": int(time.time()),
            "expires_at": int(time.time()) + long_token_response.get("expires_in", 5184000),
            "last_refresh": int(time.time())
        }
        
        update_ceo(ceo_id, {"meta_connections": meta_connections})
        
        logger.info("OAuth connection successful", extra={
            "ceo_id": ceo_id,
            "platform": platform
        })
        
        return {
            "ceo_id": ceo_id,
            "platform": platform,
            "connected": True,
            "connected_at": connection_data[f"{platform}_connected_at"],
            "expires_at": connection_data[f"{platform}_token_expires_at"]
        }
    
    except Exception as e:
        logger.error("OAuth callback handling failed", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise ValueError(f"OAuth connection failed: {str(e)}")


# ==================== Connection Status ====================

def get_connection_status(ceo_id: str, platform: str) -> Dict[str, Any]:
    """
    Get Meta OAuth connection status for CEO.
    
    Args:
        ceo_id: CEO identifier
        platform: 'whatsapp' or 'instagram'
    
    Returns:
        Connection status with expiry info
    """
    ceo = get_ceo_by_id(ceo_id)
    if not ceo:
        raise ValueError(f"CEO {ceo_id} not found")
    
    meta_connections = ceo.get("meta_connections", {})
    connection = meta_connections.get(platform, {})
    
    if not connection.get("connected"):
        return {
            "platform": platform,
            "connected": False,
            "message": f"{platform.capitalize()} not connected"
        }
    
    expires_at = connection.get("expires_at", 0)
    time_until_expiry = expires_at - int(time.time())
    days_until_expiry = time_until_expiry // 86400
    
    return {
        "platform": platform,
        "connected": True,
        "connected_at": connection.get("connected_at"),
        "expires_at": expires_at,
        "days_until_expiry": days_until_expiry,
        "needs_refresh": days_until_expiry < 7,
        "last_refresh": connection.get("last_refresh")
    }


# ==================== Token Revocation ====================

def revoke_connection(ceo_id: str, platform: str) -> bool:
    """
    Revoke Meta OAuth connection.
    
    Args:
        ceo_id: CEO identifier
        platform: 'whatsapp' or 'instagram'
    
    Returns:
        True if successful
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Delete token from Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        secret_name = f"/TrustGuard/{ceo_id}/meta/{platform}"
        
        try:
            secrets_client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Update CEO record
        ceo = get_ceo_by_id(ceo_id)
        meta_connections = ceo.get("meta_connections", {})
        
        if platform in meta_connections:
            meta_connections[platform] = {
                "connected": False,
                "disconnected_at": int(time.time())
            }
            update_ceo(ceo_id, {"meta_connections": meta_connections})
        
        logger.info("Meta connection revoked", extra={
            "ceo_id": ceo_id,
            "platform": platform
        })
        
        return True
    
    except Exception as e:
        logger.error("Failed to revoke Meta connection", extra={
            "ceo_id": ceo_id,
            "platform": platform,
            "error": str(e)
        })
        raise ValueError(f"Revocation failed: {str(e)}")
