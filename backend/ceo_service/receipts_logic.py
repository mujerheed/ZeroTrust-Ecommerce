"""
Business logic for CEO receipts management.

Provides CEO with centralized receipt oversight:
- List all receipts across vendors
- Filter by status, vendor, date range
- Bulk verification operations
- Receipt statistics and insights
- Fraud detection flags
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from common.logger import logger
from common.db_connection import dynamodb
from common.config import settings
from receipt_service.database import (
    get_receipt_by_id,
    update_receipt_status,
    get_order_by_id
)

receipts_table = dynamodb.Table(settings.RECEIPTS_TABLE)


def get_receipts_for_ceo(
    ceo_id: str,
    status: Optional[str] = None,
    vendor_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    last_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all receipts for a CEO's business with filters.
    
    Args:
        ceo_id: CEO identifier for multi-tenancy
        status: Filter by status (pending_review, approved, rejected, flagged)
        vendor_id: Filter by vendor
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (YYYY-MM-DD)
        limit: Max results per page
        last_key: Pagination token
    
    Returns:
        {
            "receipts": [...],
            "count": int,
            "last_key": str or None (for pagination),
            "has_more": bool
        }
    """
    try:
        # Use Scan with FilterExpression (CEOIndex GSI may not exist)
        scan_params = {
            'FilterExpression': 'ceo_id = :ceo_id',
            'ExpressionAttributeValues': {':ceo_id': ceo_id},
            'Limit': limit
        }
        
        # Build additional filter expressions
        filter_parts = ['ceo_id = :ceo_id']
        expr_values = scan_params['ExpressionAttributeValues']
        expr_names = {}
        
        if status:
            filter_parts.append('#status = :status')
            expr_values[':status'] = status
            expr_names['#status'] = 'status'
        
        if vendor_id:
            filter_parts.append('vendor_id = :vendor_id')
            expr_values[':vendor_id'] = vendor_id
        
        if start_date:
            filter_parts.append('upload_timestamp >= :start_date')
            expr_values[':start_date'] = f"{start_date}T00:00:00"
        
        if end_date:
            filter_parts.append('upload_timestamp <= :end_date')
            expr_values[':end_date'] = f"{end_date}T23:59:59"
        
        if len(filter_parts) > 1:
            scan_params['FilterExpression'] = ' AND '.join(filter_parts)
        
        if expr_names:
            scan_params['ExpressionAttributeNames'] = expr_names
        
        if last_key:
            scan_params['ExclusiveStartKey'] = {'receipt_id': last_key}
        
        response = receipts_table.scan(**scan_params)
        receipts = response.get('Items', [])
        
        # Sort by upload_timestamp (most recent first)
        receipts.sort(key=lambda x: x.get('upload_timestamp', ''), reverse=True)
        
        # Get pagination info
        last_evaluated_key = response.get('LastEvaluatedKey')
        next_key = last_evaluated_key.get('receipt_id') if last_evaluated_key else None
        
        logger.info(
            f"Retrieved {len(receipts)} receipts for CEO {ceo_id}",
            extra={
                'ceo_id': ceo_id,
                'count': len(receipts),
                'filters': {
                    'status': status,
                    'vendor_id': vendor_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        )
        
        return {
            'receipts': receipts,
            'count': len(receipts),
            'last_key': next_key,
            'has_more': next_key is not None
        }
    
    except Exception as e:
        logger.error(
            f"Failed to retrieve receipts for CEO: {str(e)}",
            extra={'ceo_id': ceo_id}
        )
        raise ValueError(f"Failed to retrieve receipts: {str(e)}")


def get_receipt_stats_for_ceo(ceo_id: str) -> Dict[str, Any]:
    """
    Get receipt statistics for CEO dashboard.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        {
            "total_receipts": int,
            "pending_review": int,
            "approved": int,
            "rejected": int,
            "flagged": int,
            "verification_rate": float (percentage),
            "avg_processing_time_hours": float,
            "recent_activity": [...]
        }
    """
    try:
        # Scan all receipts for this CEO
        response = receipts_table.scan(
            FilterExpression='ceo_id = :ceo_id',
            ExpressionAttributeValues={':ceo_id': ceo_id}
        )
        
        receipts = response.get('Items', [])
        total = len(receipts)
        
        if total == 0:
            return {
                'total_receipts': 0,
                'pending_review': 0,
                'approved': 0,
                'rejected': 0,
                'flagged': 0,
                'verification_rate': 0.0,
                'avg_processing_time_hours': 0.0,
                'recent_activity': []
            }
        
        # Count by status
        status_counts = {
            'pending_review': 0,
            'approved': 0,
            'rejected': 0,
            'flagged': 0
        }
        
        processing_times = []
        
        for receipt in receipts:
            status = receipt.get('status', 'pending_review')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calculate processing time for verified receipts
            if receipt.get('verified_at'):
                uploaded = datetime.fromisoformat(receipt['upload_timestamp'].replace('Z', ''))
                verified = datetime.fromisoformat(receipt['verified_at'].replace('Z', ''))
                processing_time = (verified - uploaded).total_seconds() / 3600  # hours
                processing_times.append(processing_time)
        
        # Calculate verification rate
        verified_count = status_counts['approved'] + status_counts['rejected']
        verification_rate = (verified_count / total * 100) if total > 0 else 0.0
        
        # Calculate average processing time
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Get recent activity (last 10 verified receipts)
        recent = sorted(
            [r for r in receipts if r.get('verified_at')],
            key=lambda x: x.get('verified_at', ''),
            reverse=True
        )[:10]
        
        recent_activity = [
            {
                'receipt_id': r.get('receipt_id'),
                'order_id': r.get('order_id'),
                'status': r.get('status'),
                'verified_by': r.get('verified_by'),
                'verified_at': r.get('verified_at'),
                'amount': float(r.get('amount', 0)) if r.get('amount') else None
            }
            for r in recent
        ]
        
        logger.info(
            f"Generated receipt stats for CEO {ceo_id}",
            extra={
                'ceo_id': ceo_id,
                'total': total,
                'verification_rate': verification_rate
            }
        )
        
        return {
            'total_receipts': total,
            'pending_review': status_counts['pending_review'],
            'approved': status_counts['approved'],
            'rejected': status_counts['rejected'],
            'flagged': status_counts['flagged'],
            'verification_rate': round(verification_rate, 2),
            'avg_processing_time_hours': round(avg_processing_time, 2),
            'recent_activity': recent_activity
        }
    
    except Exception as e:
        logger.error(
            f"Failed to generate receipt stats: {str(e)}",
            extra={'ceo_id': ceo_id}
        )
        raise ValueError(f"Failed to generate stats: {str(e)}")


def bulk_verify_receipts(
    ceo_id: str,
    receipt_ids: List[str],
    action: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Bulk verify receipts (approve/reject/flag).
    
    Args:
        ceo_id: CEO identifier for authorization
        receipt_ids: List of receipt IDs to process
        action: 'approve' | 'reject' | 'flag'
        notes: Optional notes for verification
    
    Returns:
        {
            "success_count": int,
            "failed_count": int,
            "results": [
                {"receipt_id": str, "success": bool, "error": str or None}
            ]
        }
    """
    if action not in ['approve', 'reject', 'flag']:
        raise ValueError(f"Invalid action: {action}. Must be 'approve', 'reject', or 'flag'")
    
    status_map = {
        'approve': 'approved',
        'reject': 'rejected',
        'flag': 'flagged'
    }
    new_status = status_map[action]
    
    results = []
    success_count = 0
    failed_count = 0
    
    for receipt_id in receipt_ids:
        try:
            # Verify receipt belongs to this CEO
            receipt = get_receipt_by_id(receipt_id)
            
            if not receipt:
                results.append({
                    'receipt_id': receipt_id,
                    'success': False,
                    'error': 'Receipt not found'
                })
                failed_count += 1
                continue
            
            if receipt.get('ceo_id') != ceo_id:
                results.append({
                    'receipt_id': receipt_id,
                    'success': False,
                    'error': 'Access denied: Receipt does not belong to your business'
                })
                failed_count += 1
                continue
            
            # Update status
            success = update_receipt_status(
                receipt_id=receipt_id,
                status=new_status,
                verified_by=ceo_id,
                notes=notes
            )
            
            if success:
                results.append({
                    'receipt_id': receipt_id,
                    'success': True,
                    'error': None
                })
                success_count += 1
            else:
                results.append({
                    'receipt_id': receipt_id,
                    'success': False,
                    'error': 'Database update failed'
                })
                failed_count += 1
        
        except Exception as e:
            results.append({
                'receipt_id': receipt_id,
                'success': False,
                'error': str(e)
            })
            failed_count += 1
    
    logger.info(
        f"Bulk {action} completed for CEO {ceo_id}",
        extra={
            'ceo_id': ceo_id,
            'action': action,
            'total': len(receipt_ids),
            'success_count': success_count,
            'failed_count': failed_count
        }
    )
    
    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'results': results
    }


def get_flagged_receipts(ceo_id: str) -> List[Dict[str, Any]]:
    """
    Get all flagged receipts requiring CEO attention.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        List of flagged receipts with details
    """
    try:
        response = receipts_table.scan(
            FilterExpression='ceo_id = :ceo_id AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':ceo_id': ceo_id,
                ':status': 'flagged'
            }
        )
        
        flagged = response.get('Items', [])
        
        # Enrich with order details
        enriched = []
        for receipt in flagged:
            order_id = receipt.get('order_id')
            order = get_order_by_id(order_id) if order_id else None
            
            enriched.append({
                **receipt,
                'order_details': order if order else None
            })
        
        logger.info(
            f"Retrieved {len(flagged)} flagged receipts for CEO {ceo_id}",
            extra={'ceo_id': ceo_id, 'count': len(flagged)}
        )
        
        return enriched
    
    except Exception as e:
        logger.error(
            f"Failed to retrieve flagged receipts: {str(e)}",
            extra={'ceo_id': ceo_id}
        )
        raise ValueError(f"Failed to retrieve flagged receipts: {str(e)}")


def get_receipt_details_for_ceo(ceo_id: str, receipt_id: str) -> Dict[str, Any]:
    """
    Get detailed receipt information with authorization check.
    
    Args:
        ceo_id: CEO identifier for authorization
        receipt_id: Receipt identifier
    
    Returns:
        Receipt details with order and buyer information
    """
    try:
        receipt = get_receipt_by_id(receipt_id)
        
        if not receipt:
            raise ValueError(f"Receipt not found: {receipt_id}")
        
        if receipt.get('ceo_id') != ceo_id:
            raise ValueError("Access denied: Receipt does not belong to your business")
        
        # Get order details
        order_id = receipt.get('order_id')
        order = get_order_by_id(order_id) if order_id else None
        
        # Get buyer details (basic info only)
        buyer_id = receipt.get('buyer_id')
        buyer_info = {
            'buyer_id': buyer_id,
            'order_count': 1  # TODO: Query buyer's total order count
        }
        
        return {
            'receipt': receipt,
            'order': order,
            'buyer': buyer_info
        }
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve receipt details: {str(e)}",
            extra={'ceo_id': ceo_id, 'receipt_id': receipt_id}
        )
        raise ValueError(f"Failed to retrieve receipt details: {str(e)}")
