"""
AWS Secrets Manager Helper for Meta OAuth Credentials

Fetches Meta APP_ID, APP_SECRET, and access tokens from Secrets Manager.

Secrets Structure (from SAM template):
- Secret Name: /TrustGuard/{Environment}/meta-{StackName}
- Secret Value (JSON):
  {
    "APP_ID": "850791007281950",
    "APP_SECRET": "5ba4cd58e7205ecd439cf49ac11c7adb",
    "ceo_oauth_tokens": {
      "ceo_123": {
        "access_token": "...",
        "expires_at": 1234567890,
        "whatsapp_phone_id": "...",
        "instagram_page_id": "..."
      }
    }
  }
"""

import json
import boto3
from typing import Dict, Any, Optional
from functools import lru_cache
from common.logger import logger
from common.config import settings


# Initialize boto3 client
secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)


@lru_cache(maxsize=1)
def get_meta_secret_name() -> str:
    """
    Get the Meta secrets name from environment or construct from stack outputs.
    
    Returns:
        Secret name (e.g., '/TrustGuard/dev/meta-TrustGuard-Dev')
    """
    # Try environment variable first
    if hasattr(settings, 'META_SECRET_NAME'):
        return settings.META_SECRET_NAME
    
    # Fallback to constructed name
    environment = getattr(settings, 'ENVIRONMENT', 'dev')
    stack_name = getattr(settings, 'STACK_NAME', 'TrustGuard-Dev')
    
    return f"/TrustGuard/{environment}/meta-{stack_name}"


async def get_meta_secrets(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Fetch Meta secrets from AWS Secrets Manager.
    
    Args:
        force_refresh: Force refresh from Secrets Manager (bypass cache)
    
    Returns:
        Dict containing APP_ID, APP_SECRET, and ceo_oauth_tokens
    
    Example:
        >>> secrets = await get_meta_secrets()
        >>> app_id = secrets.get('APP_ID')
        >>> app_secret = secrets.get('APP_SECRET')
        >>> ceo_tokens = secrets.get('ceo_oauth_tokens', {})
    """
    secret_name = get_meta_secret_name()
    
    try:
        logger.info(f"Fetching Meta secrets from: {secret_name}")
        
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        # Parse JSON secret value
        if 'SecretString' in response:
            secret_data = json.loads(response['SecretString'])
            
            logger.info("Meta secrets fetched successfully", extra={
                'has_app_id': 'APP_ID' in secret_data,
                'has_app_secret': 'APP_SECRET' in secret_data,
                'num_ceo_tokens': len(secret_data.get('ceo_oauth_tokens', {}))
            })
            
            return secret_data
        else:
            logger.error("Meta secret does not contain SecretString")
            return {}
    
    except secrets_client.exceptions.ResourceNotFoundException:
        logger.error(f"Meta secret not found: {secret_name}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching Meta secrets: {str(e)}", exc_info=True)
        return {}


async def get_ceo_oauth_token(ceo_id: str) -> Optional[Dict[str, Any]]:
    """
    Get OAuth access token for a specific CEO.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        Dict with access_token, whatsapp_phone_id, instagram_page_id, expires_at
        or None if not found
    
    Example:
        >>> token_data = await get_ceo_oauth_token("ceo_123")
        >>> access_token = token_data['access_token']
        >>> phone_id = token_data.get('whatsapp_phone_id')
    """
    secrets = await get_meta_secrets()
    ceo_tokens = secrets.get('ceo_oauth_tokens', {})
    
    token_data = ceo_tokens.get(ceo_id)
    
    if token_data:
        logger.info(f"OAuth token found for CEO: {ceo_id}")
        return token_data
    else:
        logger.warning(f"No OAuth token found for CEO: {ceo_id}")
        return None


async def update_ceo_oauth_token(
    ceo_id: str,
    access_token: str,
    whatsapp_phone_id: str = None,
    instagram_page_id: str = None,
    expires_at: int = None
) -> bool:
    """
    Update or add OAuth token for a CEO in Secrets Manager.
    
    Args:
        ceo_id: CEO identifier
        access_token: Meta access token (long-lived)
        whatsapp_phone_id: WhatsApp Business Phone Number ID
        instagram_page_id: Instagram-connected Page ID
        expires_at: Token expiration timestamp
    
    Returns:
        True if update succeeded, False otherwise
    """
    secret_name = get_meta_secret_name()
    
    try:
        # Get current secrets
        secrets = await get_meta_secrets(force_refresh=True)
        
        # Update ceo_oauth_tokens
        if 'ceo_oauth_tokens' not in secrets:
            secrets['ceo_oauth_tokens'] = {}
        
        secrets['ceo_oauth_tokens'][ceo_id] = {
            'access_token': access_token,
            'whatsapp_phone_id': whatsapp_phone_id,
            'instagram_page_id': instagram_page_id,
            'expires_at': expires_at,
            'updated_at': int(time.time())
        }
        
        # Update secret in Secrets Manager
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )
        
        logger.info(f"Updated OAuth token for CEO: {ceo_id}")
        
        # Clear cache to force refresh on next call
        get_meta_secrets.cache_clear() if hasattr(get_meta_secrets, 'cache_clear') else None
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating CEO OAuth token: {str(e)}", exc_info=True)
        return False


async def get_app_credentials() -> Dict[str, str]:
    """
    Get Meta App ID and App Secret (used for OAuth flow).
    
    Returns:
        Dict with APP_ID and APP_SECRET
    
    Example:
        >>> creds = await get_app_credentials()
        >>> app_id = creds['APP_ID']
        >>> app_secret = creds['APP_SECRET']
    """
    secrets = await get_meta_secrets()
    
    return {
        'APP_ID': secrets.get('APP_ID'),
        'APP_SECRET': secrets.get('APP_SECRET')
    }


# For synchronous contexts (non-async)
def get_meta_secrets_sync() -> Dict[str, Any]:
    """
    Synchronous version of get_meta_secrets.
    Use in non-async contexts.
    """
    secret_name = get_meta_secret_name()
    
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        else:
            return {}
    except Exception as e:
        logger.error(f"Error fetching Meta secrets (sync): {str(e)}")
        return {}


import time
