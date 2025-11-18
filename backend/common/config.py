"""
Load and validate environment variables with AWS Secrets Manager integration.

This module provides:
- Pydantic-based configuration validation
- AWS Secrets Manager integration for production secrets
- Local .env file support for development
- Fresh secret fetching (no caching) for Zero Trust compliance
"""

import os
import json
import boto3
from dotenv import load_dotenv
from pydantic import BaseSettings
from typing import Optional
from functools import lru_cache

# Load .env locally (not in Lambda)
if os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None:
    load_dotenv()


class Settings(BaseSettings):
    """
    Application settings with AWS Secrets Manager integration.
    
    Secrets are fetched fresh from Secrets Manager in production (Lambda)
    and loaded from .env file in local development.
    """
    
    # Environment
    AWS_REGION: str
    ENVIRONMENT: str = "dev"
    
    # DynamoDB Tables
    USERS_TABLE: str
    OTPS_TABLE: str
    ORDERS_TABLE: str
    AUDIT_LOGS_TABLE: str
    ESCALATIONS_TABLE: str
    CEO_MAPPING_TABLE: str
    
    # S3
    RECEIPT_BUCKET: str
    
    # Secrets (local fallback)
    JWT_SECRET: str = "dev-secret-change-in-production"
    
    # SNS
    ESCALATION_SNS_TOPIC_ARN: str = ""
    
    # Business Logic
    HIGH_VALUE_THRESHOLD: int = 1000000  # ₦1,000,000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def _is_lambda_environment(self) -> bool:
        """Check if running in AWS Lambda environment."""
        return os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
    
    def _fetch_secret(self, secret_name: str, key: Optional[str] = None) -> str:
        """
        Fetch secret from AWS Secrets Manager (no caching).
        
        Args:
            secret_name (str): Name of the secret in Secrets Manager
            key (str, optional): Key within the secret JSON. If None, returns full string.
        
        Returns:
            str: Secret value
        
        Raises:
            Exception: If secret retrieval fails
        """
        try:
            client = boto3.client('secretsmanager', region_name=self.AWS_REGION)
            response = client.get_secret_value(SecretId=secret_name)
            
            # Parse secret string
            secret_string = response['SecretString']
            
            # If key is specified, parse as JSON and extract
            if key:
                secret_dict = json.loads(secret_string)
                return secret_dict[key]
            
            return secret_string
            
        except Exception as e:
            # Log error but don't expose secret details
            print(f"Error fetching secret {secret_name}: {str(e)}")
            raise
    
    def get_jwt_secret(self) -> str:
        """
        Get JWT secret - from Secrets Manager in production, .env in development.
        
        This method fetches fresh each time (no caching) as per Zero Trust requirements.
        
        Returns:
            str: JWT secret key
        """
        if self._is_lambda_environment():
            # Production: fetch from Secrets Manager
            return self._fetch_secret('TrustGuard-JWTSecret', 'JWT_SECRET')
        
        # Development: use .env value
        return self.JWT_SECRET
    
    def get_meta_token(self, ceo_id: str) -> Optional[str]:
        """
        Get Meta API access token for a specific CEO (multi-tenant).
        
        Args:
            ceo_id (str): CEO identifier
        
        Returns:
            Optional[str]: Meta access token or None if not found
        
        Note:
            Token format in Secrets Manager: TrustGuard-Meta-{ceo_id}
            Contains: {"access_token": "...", "token_type": "...", "expires_at": ...}
        """
        if not self._is_lambda_environment():
            # Local dev: return mock token
            return os.getenv('META_ACCESS_TOKEN', 'mock_meta_token_for_dev')
        
        try:
            secret_name = f'TrustGuard-Meta-{ceo_id}'
            token_data = self._fetch_secret(secret_name, 'access_token')
            return token_data
        except Exception:
            # Token not found or expired
            return None
    
    def get_meta_app_secret(self) -> str:
        """
        Get Meta App Secret for webhook HMAC validation.
        
        Returns:
            str: Meta App Secret
        """
        if self._is_lambda_environment():
            return self._fetch_secret('TrustGuard-MetaAppSecret', 'app_secret')
        
        return os.getenv('META_APP_SECRET', 'mock_app_secret_for_dev')


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (caches everything except secrets).
    
    Returns:
        Settings: Application settings
    
    Note:
        This caches the Settings object but NOT the secrets themselves.
        Secrets are fetched fresh on each call to get_jwt_secret() etc.
    """
    return Settings()


# Global settings instance
settings = get_settings()

