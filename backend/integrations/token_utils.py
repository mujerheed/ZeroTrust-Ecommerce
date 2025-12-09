"""
Token utility functions for Meta OAuth token management.

Handles token expiry calculation, refresh via Meta API, and Secrets Manager updates.
"""

import time
import requests
from typing import Dict, Any, Optional
from common.logger import logger
import os


def get_meta_token_info(ceo_id: str) -> Dict[str, Any]:
    """
    Get Meta token information for a CEO from Secrets Manager.
    
    Args:
        ceo_id: CEO ID
    
    Returns:
        Dict with token info including access_token, expires_at, etc.
    """
    try:
        from integrations.secrets_helper import get_meta_secrets
        
        secrets = get_meta_secrets(ceo_id)
        
        # Get WhatsApp token info
        whatsapp_token = secrets.get("WHATSAPP_ACCESS_TOKEN")
        whatsapp_expires_at = secrets.get("WHATSAPP_TOKEN_EXPIRES_AT", 0)
        
        # Get Instagram token info
        instagram_token = secrets.get("INSTAGRAM_ACCESS_TOKEN")
        instagram_expires_at = secrets.get("INSTAGRAM_TOKEN_EXPIRES_AT", 0)
        
        return {
            "ceo_id": ceo_id,
            "whatsapp": {
                "access_token": whatsapp_token,
                "expires_at": whatsapp_expires_at,
                "phone_number_id": secrets.get("WHATSAPP_PHONE_NUMBER_ID")
            },
            "instagram": {
                "access_token": instagram_token,
                "expires_at": instagram_expires_at,
                "page_id": secrets.get("INSTAGRAM_PAGE_ID")
            },
            "last_refreshed_at": secrets.get("LAST_REFRESHED_AT", 0)
        }
    
    except Exception as e:
        logger.error(f"Failed to get token info for CEO {ceo_id}: {str(e)}")
        raise


def calculate_days_until_expiry(expires_at: int) -> int:
    """
    Calculate days until token expiry.
    
    Args:
        expires_at: Unix timestamp of expiry
    
    Returns:
        Number of days until expiry (negative if already expired)
    """
    if expires_at == 0:
        # No expiry set, assume needs refresh
        return 0
    
    current_time = int(time.time())
    seconds_remaining = expires_at - current_time
    days_remaining = seconds_remaining // 86400
    
    return int(days_remaining)


def refresh_meta_token(access_token: str) -> Dict[str, Any]:
    """
    Refresh Meta OAuth token via Graph API.
    
    Args:
        access_token: Current access token to refresh
    
    Returns:
        Dict with new_access_token and expires_in
    
    Raises:
        Exception if refresh fails
    """
    try:
        # Get Meta app credentials from environment
        app_id = os.getenv("META_APP_ID")
        app_secret = os.getenv("META_APP_SECRET")
        
        if not app_id or not app_secret:
            raise ValueError("META_APP_ID or META_APP_SECRET not configured")
        
        # Call Meta Graph API to exchange token
        response = requests.get(
            'https://graph.facebook.com/v18.0/oauth/access_token',
            params={
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'fb_exchange_token': access_token
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            raise Exception(f"Meta API error: {data['error'].get('message', 'Unknown error')}")
        
        new_token = data.get('access_token')
        expires_in = data.get('expires_in', 5184000)  # Default 60 days
        
        if not new_token:
            raise Exception("No access_token in Meta API response")
        
        logger.info(f"Token refreshed successfully, expires in {expires_in} seconds")
        
        return {
            'access_token': new_token,
            'expires_in': expires_in,
            'expires_at': int(time.time()) + expires_in,
            'refreshed_at': int(time.time())
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Meta API request failed: {str(e)}")
        raise Exception(f"Failed to refresh token: {str(e)}")
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise


def update_secrets_manager(ceo_id: str, platform: str, new_token_info: Dict[str, Any]) -> None:
    """
    Update Secrets Manager with new token information.
    
    Args:
        ceo_id: CEO ID
        platform: 'whatsapp' or 'instagram'
        new_token_info: Dict with access_token, expires_at, refreshed_at
    """
    try:
        import boto3
        import json
        
        # Get secret name from environment
        secret_name = os.getenv("META_SECRET_NAME")
        if not secret_name:
            raise ValueError("META_SECRET_NAME not configured")
        
        secretsmanager = boto3.client('secretsmanager')
        
        # Get current secret
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        
        # Ensure CEO section exists
        if ceo_id not in secrets:
            secrets[ceo_id] = {}
        
        # Update token based on platform
        if platform == 'whatsapp':
            secrets[ceo_id]['WHATSAPP_ACCESS_TOKEN'] = new_token_info['access_token']
            secrets[ceo_id]['WHATSAPP_TOKEN_EXPIRES_AT'] = new_token_info['expires_at']
        elif platform == 'instagram':
            secrets[ceo_id]['INSTAGRAM_ACCESS_TOKEN'] = new_token_info['access_token']
            secrets[ceo_id]['INSTAGRAM_TOKEN_EXPIRES_AT'] = new_token_info['expires_at']
        
        # Update last refreshed timestamp
        secrets[ceo_id]['LAST_REFRESHED_AT'] = new_token_info['refreshed_at']
        
        # Save updated secret
        secretsmanager.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(secrets)
        )
        
        logger.info(f"Updated {platform} token for CEO {ceo_id} in Secrets Manager")
    
    except Exception as e:
        logger.error(f"Failed to update Secrets Manager: {str(e)}")
        raise


def publish_token_expiry_metric(ceo_id: str, platform: str, days_remaining: int) -> None:
    """
    Publish CloudWatch metric for token expiry.
    
    Args:
        ceo_id: CEO ID
        platform: 'whatsapp' or 'instagram'
        days_remaining: Days until token expires
    """
    try:
        import boto3
        
        cloudwatch = boto3.client('cloudwatch')
        
        cloudwatch.put_metric_data(
            Namespace='TrustGuard/Tokens',
            MetricData=[
                {
                    'MetricName': 'DaysUntilTokenExpiry',
                    'Value': days_remaining,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'CEO', 'Value': ceo_id},
                        {'Name': 'Platform', 'Value': platform}
                    ]
                }
            ]
        )
        
        logger.debug(f"Published metric: {platform} token for {ceo_id} expires in {days_remaining} days")
    
    except Exception as e:
        logger.warning(f"Failed to publish CloudWatch metric: {str(e)}")
        # Don't raise - metric publishing failure shouldn't block token refresh
