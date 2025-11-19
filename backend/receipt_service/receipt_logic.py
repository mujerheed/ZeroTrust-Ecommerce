"""
Receipt verification business logic with auto-escalation.

Key flows:
1. Buyer uploads receipt → S3 presigned URL
2. Vendor reviews receipt → approve/reject/flag
3. High-value receipts (≥₦1M) → auto-escalate to CEO
4. Flagged receipts → CEO approval required
"""

import uuid
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from common.s3_client import receipt_storage
from common.escalation_db import create_escalation
from common.sns_client import send_escalation_alert, send_buyer_notification
from common.audit_db import log_audit_event
from common.config import settings
from common.logger import logger
from .database import (
    save_receipt_metadata,
    get_receipt_by_id,
    get_receipts_by_order,
    get_receipts_by_vendor,
    update_receipt_status,
    get_order_by_id,
    update_order_status
)


def request_receipt_upload(
    order_id: str,
    buyer_id: str,
    vendor_id: str,
    ceo_id: str,
    file_extension: str,
    content_type: str
) -> Dict[str, Any]:
    """
    Generate presigned URL for buyer to upload receipt.
    
    Args:
        order_id: Order identifier
        buyer_id: Buyer uploading receipt
        vendor_id: Vendor assigned to verify
        ceo_id: CEO for multi-tenancy
        file_extension: File extension (jpg, png, pdf)
        content_type: MIME type
    
    Returns:
        Dict with upload_url, receipt_id, and expiry info
    
    Raises:
        ValueError: If order not found or invalid params
    """
    # Validate order exists
    order = get_order_by_id(order_id)
    if not order:
        raise ValueError(f"Order not found: {order_id}")
    
    # Verify buyer owns this order
    if order.get('buyer_id') != buyer_id:
        raise ValueError(f"Buyer {buyer_id} not authorized for order {order_id}")
    
    # Generate unique receipt ID
    receipt_id = f"receipt_{uuid.uuid4().hex[:16]}"
    
    # Generate presigned upload URL
    upload_data = receipt_storage.generate_upload_url(
        ceo_id=ceo_id,
        vendor_id=vendor_id,
        order_id=order_id,
        receipt_id=receipt_id,
        file_extension=file_extension,
        content_type=content_type
    )
    
    logger.info(
        f"Generated upload URL for receipt {receipt_id}",
        extra={
            'receipt_id': receipt_id,
            'order_id': order_id,
            'buyer_id': buyer_id,
            'vendor_id': vendor_id
        }
    )
    
    return {
        'receipt_id': receipt_id,
        'upload_url': upload_data['upload_url'],
        's3_key': upload_data['s3_key'],
        'expires_in': upload_data['expires_in'],
        'max_file_size': upload_data['max_file_size'],
        'allowed_content_types': upload_data['allowed_content_types']
    }


def confirm_receipt_upload(
    receipt_id: str,
    s3_key: str,
    order_id: str,
    buyer_id: str,
    vendor_id: str,
    ceo_id: str
) -> Dict[str, Any]:
    """
    Confirm receipt upload and save metadata to DynamoDB.
    
    Args:
        receipt_id: Receipt identifier
        s3_key: S3 location of uploaded file
        order_id: Associated order
        buyer_id: Buyer who uploaded
        vendor_id: Vendor to review
        ceo_id: CEO for multi-tenancy
    
    Returns:
        Dict with receipt_id and status
    
    Raises:
        ValueError: If upload not found in S3
    """
    # Verify file exists in S3
    if not receipt_storage.verify_upload_completed(s3_key):
        raise ValueError(f"Receipt upload not found in S3: {s3_key}")
    
    # Get file metadata from S3
    file_metadata = receipt_storage.get_receipt_metadata(s3_key)
    if not file_metadata:
        raise ValueError(f"Failed to retrieve receipt metadata from S3")
    
    # Save to DynamoDB
    success = save_receipt_metadata(
        receipt_id=receipt_id,
        order_id=order_id,
        buyer_id=buyer_id,
        vendor_id=vendor_id,
        ceo_id=ceo_id,
        s3_key=s3_key,
        file_size=file_metadata['file_size'],
        content_type=file_metadata['content_type']
    )
    
    if not success:
        raise Exception("Failed to save receipt metadata")
    
    # Log audit event
    log_audit_event(
        user_id=buyer_id,
        action='RECEIPT_UPLOADED',
        resource_type='receipt',
        resource_id=receipt_id,
        details={
            'order_id': order_id,
            'vendor_id': vendor_id,
            'file_size': file_metadata['file_size'],
            'content_type': file_metadata['content_type']
        },
        ceo_id=ceo_id
    )
    
    logger.info(
        f"Receipt upload confirmed: {receipt_id}",
        extra={
            'receipt_id': receipt_id,
            'order_id': order_id,
            'file_size': file_metadata['file_size']
        }
    )
    
    return {
        'receipt_id': receipt_id,
        'status': 'pending_review',
        'message': 'Receipt uploaded successfully. Vendor will review shortly.'
    }


def vendor_verify_receipt(
    receipt_id: str,
    vendor_id: str,
    action: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Vendor reviews and approves/rejects/flags a receipt.
    
    High-value logic:
    - If amount ≥ ₦1,000,000 AND action is 'approve' → auto-escalate to CEO
    - If action is 'flag' → escalate to CEO for review
    
    Args:
        receipt_id: Receipt to verify
        vendor_id: Vendor performing verification
        action: 'approve' | 'reject' | 'flag'
        notes: Verification notes (required for reject/flag)
    
    Returns:
        Dict with status and next steps
    
    Raises:
        ValueError: If receipt not found or vendor unauthorized
    """
    if action not in ['approve', 'reject', 'flag']:
        raise ValueError(f"Invalid action: {action}. Must be approve, reject, or flag")
    
    if action in ['reject', 'flag'] and not notes:
        raise ValueError(f"Notes are required when action is '{action}'")
    
    # Get receipt
    receipt = get_receipt_by_id(receipt_id)
    if not receipt:
        raise ValueError(f"Receipt not found: {receipt_id}")
    
    # Verify vendor is assigned
    if receipt.get('vendor_id') != vendor_id:
        raise ValueError(f"Vendor {vendor_id} not authorized for receipt {receipt_id}")
    
    # Check if already verified
    if receipt.get('status') != 'pending_review':
        raise ValueError(f"Receipt already processed with status: {receipt['status']}")
    
    order_id = receipt['order_id']
    ceo_id = receipt['ceo_id']
    buyer_id = receipt['buyer_id']
    
    # Get order to check amount
    order = get_order_by_id(order_id)
    order_amount = Decimal(str(order.get('amount', 0)))
    
    # HIGH-VALUE ESCALATION LOGIC
    high_value_threshold = Decimal(str(settings.HIGH_VALUE_THRESHOLD))
    requires_ceo_approval = (
        order_amount >= high_value_threshold or 
        action == 'flag'
    )
    
    if requires_ceo_approval:
        # Create escalation
        escalation_reason = 'high_value' if order_amount >= high_value_threshold else 'flagged_by_vendor'
        
        escalation_id = create_escalation(
            order_id=order_id,
            ceo_id=ceo_id,
            vendor_id=vendor_id,
            buyer_id=buyer_id,
            reason=escalation_reason,
            amount=order_amount,
            vendor_notes=notes or f"Receipt {action}ed by vendor"
        )
        
        # Update receipt status to flagged
        update_receipt_status(
            receipt_id=receipt_id,
            status='flagged',
            verified_by=vendor_id,
            notes=notes
        )
        
        # Send escalation alert to CEO
        send_escalation_alert(
            ceo_id=ceo_id,
            escalation_id=escalation_id,
            order_id=order_id,
            amount=float(order_amount),
            reason=escalation_reason
        )
        
        # Log audit event
        log_audit_event(
            user_id=vendor_id,
            action='RECEIPT_ESCALATED',
            resource_type='receipt',
            resource_id=receipt_id,
            details={
                'escalation_id': escalation_id,
                'reason': escalation_reason,
                'amount': str(order_amount),
                'notes': notes
            },
            ceo_id=ceo_id
        )
        
        logger.warning(
            f"Receipt {receipt_id} escalated to CEO",
            extra={
                'receipt_id': receipt_id,
                'escalation_id': escalation_id,
                'reason': escalation_reason,
                'amount': str(order_amount)
            }
        )
        
        return {
            'status': 'escalated',
            'escalation_id': escalation_id,
            'message': f'Receipt escalated to CEO for approval. Reason: {escalation_reason}',
            'requires_ceo_approval': True
        }
    
    else:
        # Normal vendor verification (no CEO approval needed)
        new_status = 'approved' if action == 'approve' else 'rejected'
        
        # Update receipt status
        update_receipt_status(
            receipt_id=receipt_id,
            status=new_status,
            verified_by=vendor_id,
            notes=notes
        )
        
        # Update order status
        if action == 'approve':
            update_order_status(order_id, 'verified')
        else:
            update_order_status(order_id, 'cancelled')
        
        # Notify buyer
        send_buyer_notification(
            buyer_id=buyer_id,
            message=f"Your receipt for order {order_id} has been {new_status}.",
            notification_type='receipt_verification'
        )
        
        # Log audit event
        log_audit_event(
            user_id=vendor_id,
            action=f'RECEIPT_{new_status.upper()}',
            resource_type='receipt',
            resource_id=receipt_id,
            details={
                'order_id': order_id,
                'action': action,
                'notes': notes
            },
            ceo_id=ceo_id
        )
        
        logger.info(
            f"Receipt {receipt_id} {new_status} by vendor",
            extra={
                'receipt_id': receipt_id,
                'vendor_id': vendor_id,
                'status': new_status
            }
        )
        
        return {
            'status': new_status,
            'message': f'Receipt {new_status}. Order updated accordingly.',
            'requires_ceo_approval': False
        }


def get_vendor_pending_receipts(vendor_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get all pending receipts for a vendor to review.
    
    Args:
        vendor_id: Vendor identifier
        limit: Max results
    
    Returns:
        Dict with receipts list and count
    """
    receipts = get_receipts_by_vendor(vendor_id, status='pending_review', limit=limit)
    
    # Enrich with download URLs
    for receipt in receipts:
        receipt['download_url'] = receipt_storage.generate_download_url(
            s3_key=receipt['s3_key'],
            expires_in=3600  # 1 hour for vendor review
        )
    
    logger.info(
        f"Retrieved {len(receipts)} pending receipts for vendor {vendor_id}",
        extra={'vendor_id': vendor_id, 'count': len(receipts)}
    )
    
    return {
        'receipts': receipts,
        'count': len(receipts),
        'vendor_id': vendor_id
    }


def get_receipt_details(receipt_id: str, user_id: str, user_role: str) -> Dict[str, Any]:
    """
    Get receipt details with download URL (authorized users only).
    
    Args:
        receipt_id: Receipt identifier
        user_id: User requesting details
        user_role: User role (Vendor, CEO, Buyer)
    
    Returns:
        Receipt details with download URL
    
    Raises:
        ValueError: If receipt not found or user unauthorized
    """
    receipt = get_receipt_by_id(receipt_id)
    if not receipt:
        raise ValueError(f"Receipt not found: {receipt_id}")
    
    # Authorization check
    authorized = False
    if user_role == 'CEO' and receipt.get('ceo_id') == user_id:
        authorized = True
    elif user_role == 'Vendor' and receipt.get('vendor_id') == user_id:
        authorized = True
    elif user_role == 'Buyer' and receipt.get('buyer_id') == user_id:
        authorized = True
    
    if not authorized:
        raise ValueError(f"User {user_id} not authorized to view receipt {receipt_id}")
    
    # Generate download URL
    receipt['download_url'] = receipt_storage.generate_download_url(
        s3_key=receipt['s3_key'],
        expires_in=3600  # 1 hour
    )
    
    logger.info(
        f"Retrieved receipt details: {receipt_id}",
        extra={'receipt_id': receipt_id, 'user_id': user_id, 'user_role': user_role}
    )
    
    return receipt
