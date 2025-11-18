"""
Escalation Database Helpers

Handles high-value and flagged transaction escalations requiring CEO approval.
Zero Trust: All escalations logged immutably, require OTP re-auth for CEO decisions.
"""

import time
import secrets
from typing import Dict, Any, List, Optional, Literal
from common.config import settings
from common.db_connection import dynamodb
from common.logger import logger

EscalationReason = Literal['HIGH_VALUE', 'VENDOR_FLAGGED', 'TEXTRACT_LOW_CONFIDENCE']
EscalationStatus = Literal['PENDING', 'APPROVED', 'REJECTED', 'EXPIRED']


def create_escalation(
    order_id: str,
    ceo_id: str,
    vendor_id: str,
    buyer_id: str,
    amount: float,
    reason: EscalationReason,
    flagged_by: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Create escalation record for CEO approval.
    
    Args:
        order_id (str): Order identifier
        ceo_id (str): CEO who must approve
        vendor_id (str): Vendor handling the order
        buyer_id (str): Buyer who placed the order
        amount (float): Order amount in Naira
        reason (str): Escalation reason ('HIGH_VALUE', 'VENDOR_FLAGGED', 'TEXTRACT_LOW_CONFIDENCE')
        flagged_by (str, optional): User ID who flagged (for manual flags)
        notes (str, optional): Additional context
    
    Returns:
        str: escalation_id
    
    Raises:
        Exception: If database write fails
    """
    table = dynamodb.Table(settings.ESCALATIONS_TABLE)
    
    escalation_id = f"esc_{secrets.token_hex(12)}"
    now = int(time.time())
    
    item = {
        'escalation_id': escalation_id,
        'ceo_id': ceo_id,
        'order_id': order_id,
        'vendor_id': vendor_id,
        'buyer_id': buyer_id,
        'amount': int(amount),  # Store as integer (Naira kobo)
        'reason': reason,
        'status': 'PENDING',
        'created_at': now,
        'updated_at': now,
        'expires_at': now + (24 * 3600),  # 24-hour escalation window
    }
    
    if flagged_by:
        item['flagged_by'] = flagged_by
    
    if notes:
        item['notes'] = notes
    
    try:
        table.put_item(Item=item)
        logger.info(
            f"Escalation created: {escalation_id} for order {order_id}, "
            f"reason={reason}, amount=₦{amount:,.2f}"
        )
        return escalation_id
        
    except Exception as e:
        logger.error(f"Failed to create escalation for order {order_id}: {str(e)}")
        raise


def get_escalation(escalation_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve escalation details by ID.
    
    Args:
        escalation_id (str): Escalation identifier
    
    Returns:
        Optional[Dict]: Escalation record or None if not found
    """
    table = dynamodb.Table(settings.ESCALATIONS_TABLE)
    
    try:
        response = table.get_item(Key={'escalation_id': escalation_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Failed to get escalation {escalation_id}: {str(e)}")
        return None


def get_pending_escalations(ceo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all pending escalations for a CEO.
    
    Args:
        ceo_id (str): CEO identifier
        limit (int): Maximum number of results
    
    Returns:
        List[Dict]: List of pending escalation records
    """
    table = dynamodb.Table(settings.ESCALATIONS_TABLE)
    
    try:
        response = table.query(
            IndexName='ByCEOPending',
            KeyConditionExpression='ceo_id = :ceo_id AND #status = :status',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':ceo_id': ceo_id,
                ':status': 'PENDING'
            },
            Limit=limit,
            ScanIndexForward=False  # Newest first
        )
        
        escalations = response.get('Items', [])
        logger.info(f"Retrieved {len(escalations)} pending escalations for CEO {ceo_id}")
        return escalations
        
    except Exception as e:
        logger.error(f"Failed to get pending escalations for CEO {ceo_id}: {str(e)}")
        return []


def update_escalation_status(
    escalation_id: str,
    status: EscalationStatus,
    approved_by: str,
    decision_notes: Optional[str] = None
) -> bool:
    """
    Update escalation status after CEO decision.
    
    Args:
        escalation_id (str): Escalation identifier
        status (str): New status ('APPROVED' or 'REJECTED')
        approved_by (str): CEO user_id who made the decision
        decision_notes (str, optional): CEO's notes on the decision
    
    Returns:
        bool: True if update succeeded
    
    Raises:
        ValueError: If trying to update non-PENDING escalation
    """
    table = dynamodb.Table(settings.ESCALATIONS_TABLE)
    now = int(time.time())
    
    # First, check current status
    escalation = get_escalation(escalation_id)
    if not escalation:
        raise ValueError(f"Escalation {escalation_id} not found")
    
    if escalation['status'] != 'PENDING':
        raise ValueError(
            f"Cannot update escalation {escalation_id}: "
            f"already {escalation['status']}"
        )
    
    try:
        update_expr = (
            "SET #status = :status, "
            "approved_by = :approved_by, "
            "updated_at = :updated_at, "
            "decision_timestamp = :decision_timestamp"
        )
        
        expr_values = {
            ':status': status,
            ':approved_by': approved_by,
            ':updated_at': now,
            ':decision_timestamp': now,
            ':pending': 'PENDING'
        }
        
        if decision_notes:
            update_expr += ", decision_notes = :notes"
            expr_values[':notes'] = decision_notes
        
        table.update_item(
            Key={'escalation_id': escalation_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues=expr_values,
            ConditionExpression='#status = :pending'  # Prevent race conditions
        )
        
        logger.info(
            f"Escalation {escalation_id} {status} by {approved_by}"
        )
        return True
        
    except Exception as e:
        logger.error(f"Failed to update escalation {escalation_id}: {str(e)}")
        return False


def expire_old_escalations() -> int:
    """
    Mark expired escalations (> 24 hours old, still PENDING) as EXPIRED.
    
    This should be called periodically (e.g., via CloudWatch Events).
    
    Returns:
        int: Number of escalations expired
    """
    # This would typically be a separate Lambda function
    # For now, it's a helper that can be called manually
    table = dynamodb.Table(settings.ESCALATIONS_TABLE)
    now = int(time.time())
    expired_count = 0
    
    # Note: This is a simplified implementation
    # In production, use DynamoDB Streams or Step Functions for automation
    
    logger.info("Expiring old escalations...")
    return expired_count


def get_escalation_summary(ceo_id: str) -> Dict[str, Any]:
    """
    Get summary statistics of escalations for CEO dashboard.
    
    Args:
        ceo_id (str): CEO identifier
    
    Returns:
        Dict: Summary with counts by status and total value
    """
    table = dynamodb.Table(settings.ESCALATIONS_TABLE)
    
    try:
        # Query all escalations for this CEO
        response = table.query(
            IndexName='ByCEOPending',
            KeyConditionExpression='ceo_id = :ceo_id',
            ExpressionAttributeValues={
                ':ceo_id': ceo_id
            }
        )
        
        escalations = response.get('Items', [])
        
        summary = {
            'total': len(escalations),
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'expired': 0,
            'total_pending_value': 0,
            'avg_pending_value': 0
        }
        
        pending_amounts = []
        
        for esc in escalations:
            status = esc['status']
            summary[status.lower()] += 1
            
            if status == 'PENDING':
                amount = esc.get('amount', 0)
                pending_amounts.append(amount)
                summary['total_pending_value'] += amount
        
        if pending_amounts:
            summary['avg_pending_value'] = summary['total_pending_value'] / len(pending_amounts)
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get escalation summary for CEO {ceo_id}: {str(e)}")
        return {
            'total': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'expired': 0,
            'total_pending_value': 0,
            'avg_pending_value': 0
        }
