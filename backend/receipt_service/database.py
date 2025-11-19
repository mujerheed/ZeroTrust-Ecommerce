"""
Database operations for receipt management.

Tables used:
- TrustGuard-Receipts: Receipt metadata and verification status
- TrustGuard-Orders: Order details (linked to receipts)
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal
from common.db_connection import dynamodb
from common.config import settings
from common.logger import logger

# Initialize table
receipts_table = dynamodb.Table(settings.RECEIPTS_TABLE)
orders_table = dynamodb.Table(settings.ORDERS_TABLE)


def save_receipt_metadata(
    receipt_id: str,
    order_id: str,
    buyer_id: str,
    vendor_id: str,
    ceo_id: str,
    s3_key: str,
    file_size: int,
    content_type: str,
    amount: Optional[Decimal] = None
) -> bool:
    """
    Save receipt metadata to DynamoDB.
    
    Args:
        receipt_id: Unique receipt identifier
        order_id: Associated order ID
        buyer_id: Buyer who uploaded receipt
        vendor_id: Vendor assigned to verify
        ceo_id: CEO for multi-tenancy
        s3_key: S3 location of receipt file
        file_size: File size in bytes
        content_type: MIME type
        amount: Transaction amount (optional, from Textract)
    
    Returns:
        True if saved successfully
    """
    try:
        item = {
            'receipt_id': receipt_id,
            'order_id': order_id,
            'buyer_id': buyer_id,
            'vendor_id': vendor_id,
            'ceo_id': ceo_id,
            's3_key': s3_key,
            'file_size': file_size,
            'content_type': content_type,
            'upload_timestamp': datetime.utcnow().isoformat(),
            'status': 'pending_review',  # pending_review | approved | rejected | flagged
            'verification_notes': None,
            'verified_by': None,
            'verified_at': None,
            'textract_data': None,
            'ocr_confidence': None
        }
        
        if amount:
            item['amount'] = amount
        
        receipts_table.put_item(Item=item)
        
        logger.info(
            f"Saved receipt metadata: {receipt_id}",
            extra={
                'receipt_id': receipt_id,
                'order_id': order_id,
                'buyer_id': buyer_id,
                'vendor_id': vendor_id
            }
        )
        
        return True
    
    except Exception as e:
        logger.error(
            f"Failed to save receipt metadata: {str(e)}",
            extra={'receipt_id': receipt_id, 'order_id': order_id}
        )
        return False


def get_receipt_by_id(receipt_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve receipt metadata by ID.
    
    Args:
        receipt_id: Unique receipt identifier
    
    Returns:
        Receipt metadata dict or None
    """
    try:
        response = receipts_table.get_item(Key={'receipt_id': receipt_id})
        receipt = response.get('Item')
        
        if receipt:
            logger.info(f"Retrieved receipt: {receipt_id}")
        else:
            logger.warning(f"Receipt not found: {receipt_id}")
        
        return receipt
    
    except Exception as e:
        logger.error(f"Failed to retrieve receipt: {str(e)}", extra={'receipt_id': receipt_id})
        return None


def get_receipts_by_order(order_id: str) -> List[Dict[str, Any]]:
    """
    Get all receipts for a specific order.
    
    Args:
        order_id: Order identifier
    
    Returns:
        List of receipt metadata dicts
    """
    try:
        # Query using OrderIndex GSI
        response = receipts_table.query(
            IndexName='OrderIndex',
            KeyConditionExpression='order_id = :order_id',
            ExpressionAttributeValues={':order_id': order_id}
        )
        
        receipts = response.get('Items', [])
        
        logger.info(
            f"Retrieved {len(receipts)} receipts for order {order_id}",
            extra={'order_id': order_id, 'count': len(receipts)}
        )
        
        return receipts
    
    except Exception as e:
        logger.error(f"Failed to query receipts by order: {str(e)}", extra={'order_id': order_id})
        return []


def get_receipts_by_vendor(vendor_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get receipts assigned to a vendor for review.
    
    Args:
        vendor_id: Vendor identifier
        status: Filter by status (optional)
        limit: Max results to return
    
    Returns:
        List of receipt metadata dicts
    """
    try:
        # Query using VendorIndex GSI
        query_params = {
            'IndexName': 'VendorIndex',
            'KeyConditionExpression': 'vendor_id = :vendor_id',
            'ExpressionAttributeValues': {':vendor_id': vendor_id},
            'Limit': limit,
            'ScanIndexForward': False  # Most recent first
        }
        
        if status:
            query_params['FilterExpression'] = '#status = :status'
            query_params['ExpressionAttributeNames'] = {'#status': 'status'}
            query_params['ExpressionAttributeValues'][':status'] = status
        
        response = receipts_table.query(**query_params)
        receipts = response.get('Items', [])
        
        logger.info(
            f"Retrieved {len(receipts)} receipts for vendor {vendor_id}",
            extra={'vendor_id': vendor_id, 'status': status, 'count': len(receipts)}
        )
        
        return receipts
    
    except Exception as e:
        logger.error(
            f"Failed to query receipts by vendor: {str(e)}",
            extra={'vendor_id': vendor_id}
        )
        return []


def update_receipt_status(
    receipt_id: str,
    status: str,
    verified_by: str,
    notes: Optional[str] = None
) -> bool:
    """
    Update receipt verification status.
    
    Args:
        receipt_id: Receipt identifier
        status: New status (approved | rejected | flagged)
        verified_by: Vendor or CEO who verified
        notes: Verification notes (optional)
    
    Returns:
        True if updated successfully
    """
    try:
        update_expr = 'SET #status = :status, verified_by = :verified_by, verified_at = :verified_at'
        expr_values = {
            ':status': status,
            ':verified_by': verified_by,
            ':verified_at': datetime.utcnow().isoformat()
        }
        expr_names = {'#status': 'status'}
        
        if notes:
            update_expr += ', verification_notes = :notes'
            expr_values[':notes'] = notes
        
        receipts_table.update_item(
            Key={'receipt_id': receipt_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )
        
        logger.info(
            f"Updated receipt {receipt_id} status to {status}",
            extra={
                'receipt_id': receipt_id,
                'status': status,
                'verified_by': verified_by
            }
        )
        
        return True
    
    except Exception as e:
        logger.error(
            f"Failed to update receipt status: {str(e)}",
            extra={'receipt_id': receipt_id, 'status': status}
        )
        return False


def add_textract_data(
    receipt_id: str,
    textract_data: Dict[str, Any],
    confidence: float
) -> bool:
    """
    Add Textract OCR data to receipt metadata.
    
    Args:
        receipt_id: Receipt identifier
        textract_data: Extracted data from Textract (amount, bank, date, etc.)
        confidence: Overall confidence score (0-100)
    
    Returns:
        True if updated successfully
    """
    try:
        receipts_table.update_item(
            Key={'receipt_id': receipt_id},
            UpdateExpression='SET textract_data = :data, ocr_confidence = :confidence',
            ExpressionAttributeValues={
                ':data': textract_data,
                ':confidence': Decimal(str(confidence))
            }
        )
        
        logger.info(
            f"Added Textract data to receipt {receipt_id}",
            extra={
                'receipt_id': receipt_id,
                'confidence': confidence,
                'extracted_amount': textract_data.get('amount')
            }
        )
        
        return True
    
    except Exception as e:
        logger.error(
            f"Failed to add Textract data: {str(e)}",
            extra={'receipt_id': receipt_id}
        )
        return False


def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve order details by ID.
    
    Args:
        order_id: Order identifier
    
    Returns:
        Order dict or None
    """
    try:
        response = orders_table.get_item(Key={'order_id': order_id})
        order = response.get('Item')
        
        if order:
            logger.info(f"Retrieved order: {order_id}")
        else:
            logger.warning(f"Order not found: {order_id}")
        
        return order
    
    except Exception as e:
        logger.error(f"Failed to retrieve order: {str(e)}", extra={'order_id': order_id})
        return None


def update_order_status(order_id: str, status: str) -> bool:
    """
    Update order status.
    
    Args:
        order_id: Order identifier
        status: New status (pending | verified | completed | cancelled)
    
    Returns:
        True if updated successfully
    """
    try:
        orders_table.update_item(
            Key={'order_id': order_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(
            f"Updated order {order_id} status to {status}",
            extra={'order_id': order_id, 'status': status}
        )
        
        return True
    
    except Exception as e:
        logger.error(
            f"Failed to update order status: {str(e)}",
            extra={'order_id': order_id, 'status': status}
        )
        return False
