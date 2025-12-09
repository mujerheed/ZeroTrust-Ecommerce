"""
PDF Upload and Distribution Module.

Handles uploading generated PDFs to S3 and sending download links to buyers.
"""

from typing import Dict, Any
import os
import time
from common.s3_client import s3_client
from common.logger import logger


def upload_pdf_to_s3(
    pdf_path: str,
    order_id: str,
    ceo_id: str,
    bucket_name: str = None
) -> Dict[str, str]:
    """
    Upload PDF to S3 and generate pre-signed download URL.
    
    Args:
        pdf_path: Local path to PDF file
        order_id: Order ID
        ceo_id: CEO ID for folder organization
        bucket_name: Optional S3 bucket name (defaults to env var)
    
    Returns:
        Dict with s3_key, download_url, and expires_at
    """
    try:
        # Get bucket name from environment if not provided
        if not bucket_name:
            bucket_name = os.getenv("RECEIPT_BUCKET_NAME")
            if not bucket_name:
                raise ValueError("RECEIPT_BUCKET_NAME not configured")
        
        # Generate S3 key
        timestamp = int(time.time())
        s3_key = f"pdfs/{ceo_id}/{order_id}/order_confirmation_{timestamp}.pdf"
        
        # Upload to S3
        with open(pdf_path, 'rb') as pdf_file:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=pdf_file,
                ContentType='application/pdf',
                ServerSideEncryption='aws:kms',
                Metadata={
                    'order_id': order_id,
                    'ceo_id': ceo_id,
                    'generated_at': str(timestamp)
                }
            )
        
        logger.info(f"PDF uploaded to S3: {s3_key}", extra={"order_id": order_id})
        
        # Generate pre-signed URL (24 hour expiry)
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_key
            },
            ExpiresIn=86400  # 24 hours
        )
        
        expires_at = int(time.time()) + 86400
        
        return {
            "s3_key": s3_key,
            "download_url": download_url,
            "expires_at": expires_at,
            "bucket": bucket_name
        }
    
    except Exception as e:
        logger.error(f"Failed to upload PDF to S3: {str(e)}", exc_info=True)
        raise


def cleanup_temp_pdf(pdf_path: str) -> None:
    """
    Delete temporary PDF file after upload.
    
    Args:
        pdf_path: Path to PDF file to delete
    """
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.debug(f"Cleaned up temp PDF: {pdf_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp PDF {pdf_path}: {str(e)}")


async def generate_and_send_pdf(order_id: str) -> Dict[str, Any]:
    """
    Complete workflow: Generate PDF, upload to S3, send to buyer.
    
    Args:
        order_id: Order ID to generate PDF for
    
    Returns:
        Dict with PDF generation and delivery status
    """
    try:
        from order_service.pdf_generator import generate_order_pdf
        from order_service.database import get_order_by_id
        from integrations.chatbot_router import send_pdf_confirmation
        
        # Get order details
        order = get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        ceo_id = order.get("ceo_id")
        buyer_id = order.get("buyer_id")
        
        if not ceo_id or not buyer_id:
            raise ValueError(f"Order {order_id} missing ceo_id or buyer_id")
        
        # Generate PDF
        logger.info(f"Generating PDF for order {order_id}")
        pdf_path = generate_order_pdf(order_id)
        
        # Upload to S3
        logger.info(f"Uploading PDF to S3 for order {order_id}")
        upload_result = upload_pdf_to_s3(pdf_path, order_id, ceo_id)
        
        # Clean up temp file
        cleanup_temp_pdf(pdf_path)
        
        # Send download link to buyer via chatbot
        logger.info(f"Sending PDF download link to buyer {buyer_id}")
        await send_pdf_confirmation(
            buyer_id=buyer_id,
            order_id=order_id,
            download_url=upload_result["download_url"],
            ceo_id=ceo_id
        )
        
        logger.info(f"PDF generated and sent successfully for order {order_id}")
        
        return {
            "status": "success",
            "order_id": order_id,
            "s3_key": upload_result["s3_key"],
            "download_url": upload_result["download_url"],
            "expires_at": upload_result["expires_at"],
            "sent_to_buyer": True
        }
    
    except Exception as e:
        logger.error(f"Failed to generate and send PDF for order {order_id}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "order_id": order_id,
            "error": str(e),
            "sent_to_buyer": False
        }
