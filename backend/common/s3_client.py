"""
S3 client for secure receipt storage with presigned URLs.

Security features:
- Server-side encryption (SSE-KMS or SSE-S3)
- Presigned URLs with short expiry (5 minutes)
- Content-type validation (images only)
- File size limits (max 5MB)
- Organized key structure for multi-tenancy isolation
"""

import boto3
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from .config import settings
from .logger import logger

# Initialize S3 client
s3_client = boto3.client('s3', region_name=settings.AWS_REGION)


class ReceiptStorageService:
    """
    Secure receipt storage service using S3.
    
    Key structure: receipts/{ceo_id}/{vendor_id}/{order_id}/{receipt_id}_{timestamp}.{ext}
    """
    
    ALLOWED_CONTENT_TYPES = [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/webp',
        'application/pdf'
    ]
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    PRESIGNED_URL_EXPIRY = 300  # 5 minutes
    
    def __init__(self):
        self.bucket_name = settings.RECEIPT_BUCKET
        self.s3_client = s3_client
    
    def generate_upload_url(
        self,
        ceo_id: str,
        vendor_id: str,
        order_id: str,
        receipt_id: str,
        file_extension: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Generate presigned PUT URL for buyer to upload receipt.
        
        Args:
            ceo_id: CEO identifier for multi-tenancy
            vendor_id: Vendor handling the order
            order_id: Order identifier
            receipt_id: Unique receipt identifier
            file_extension: File extension (jpg, png, pdf)
            content_type: MIME type of the file
        
        Returns:
            dict with 'upload_url', 's3_key', 'expires_in'
        
        Raises:
            ValueError: If content_type is not allowed
        """
        # Validate content type
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Content type {content_type} not allowed. "
                f"Allowed types: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )
        
        # Generate S3 key with timestamp for uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"receipts/{ceo_id}/{vendor_id}/{order_id}/{receipt_id}_{timestamp}.{file_extension}"
        
        try:
            # Generate presigned PUT URL with constraints
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type,
                    'ServerSideEncryption': 'AES256',  # SSE-S3 encryption
                    'ContentLengthRange': [1, self.MAX_FILE_SIZE]  # 1 byte to 5MB
                },
                ExpiresIn=self.PRESIGNED_URL_EXPIRY,
                HttpMethod='PUT'
            )
            
            logger.info(
                f"Generated presigned upload URL for receipt {receipt_id}",
                extra={
                    'receipt_id': receipt_id,
                    'order_id': order_id,
                    'vendor_id': vendor_id,
                    'ceo_id': ceo_id,
                    's3_key': s3_key,
                    'expires_in': self.PRESIGNED_URL_EXPIRY
                }
            )
            
            return {
                'upload_url': presigned_url,
                's3_key': s3_key,
                'expires_in': self.PRESIGNED_URL_EXPIRY,
                'max_file_size': self.MAX_FILE_SIZE,
                'allowed_content_types': self.ALLOWED_CONTENT_TYPES
            }
        
        except ClientError as e:
            logger.error(
                f"Failed to generate presigned URL: {str(e)}",
                extra={'receipt_id': receipt_id, 'order_id': order_id}
            )
            raise
    
    def generate_download_url(
        self,
        s3_key: str,
        expires_in: int = 300
    ) -> str:
        """
        Generate presigned GET URL for authorized users to view receipt.
        
        Args:
            s3_key: S3 key of the receipt
            expires_in: URL expiry in seconds (default 5 minutes)
        
        Returns:
            Presigned download URL
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in,
                HttpMethod='GET'
            )
            
            logger.info(
                f"Generated presigned download URL",
                extra={'s3_key': s3_key, 'expires_in': expires_in}
            )
            
            return presigned_url
        
        except ClientError as e:
            logger.error(
                f"Failed to generate download URL: {str(e)}",
                extra={'s3_key': s3_key}
            )
            raise
    
    def verify_upload_completed(self, s3_key: str) -> bool:
        """
        Verify that a file exists in S3 (upload was successful).
        
        Args:
            s3_key: S3 key of the receipt
        
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Verified receipt upload: {s3_key}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Receipt not found in S3: {s3_key}")
                return False
            else:
                logger.error(f"Error verifying receipt: {str(e)}", extra={'s3_key': s3_key})
                raise
    
    def get_receipt_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get receipt file metadata from S3.
        
        Args:
            s3_key: S3 key of the receipt
        
        Returns:
            Dict with file size, content type, last modified, etc.
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'file_size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'server_side_encryption': response.get('ServerSideEncryption')
            }
        
        except ClientError as e:
            logger.error(f"Failed to get receipt metadata: {str(e)}", extra={'s3_key': s3_key})
            return None
    
    def delete_receipt(self, s3_key: str) -> bool:
        """
        Delete receipt from S3 (use with caution - for compliance/GDPR only).
        
        Args:
            s3_key: S3 key of the receipt
        
        Returns:
            True if deleted successfully
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.warning(
                f"Receipt deleted from S3: {s3_key}",
                extra={'s3_key': s3_key, 'action': 'DELETE_RECEIPT'}
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to delete receipt: {str(e)}", extra={'s3_key': s3_key})
            return False


# Singleton instance
receipt_storage = ReceiptStorageService()
