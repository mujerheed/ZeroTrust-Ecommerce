"""
Immutable audit logging to DynamoDB.

All security-critical actions are logged for compliance and forensics.
Audit logs are write-only (no updates/deletes allowed).
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from common.db_connection import dynamodb
from common.config import settings
from common.logger import logger

# Initialize audit logs table
audit_logs_table = dynamodb.Table(settings.AUDIT_LOGS_TABLE)


def log_audit_event(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ceo_id: Optional[str] = None,
    ip_address: Optional[str] = None
) -> str:
    """
    Log an immutable audit event to DynamoDB.
    
    Args:
        user_id: User who performed the action
        action: Action type (e.g., RECEIPT_UPLOADED, ESCALATION_APPROVED)
        resource_type: Type of resource (receipt, order, escalation, etc.)
        resource_id: Identifier of the resource
        details: Additional context (optional)
        ceo_id: CEO for multi-tenancy (optional)
        ip_address: User's IP address (optional)
    
    Returns:
        audit_log_id: Unique identifier for the audit event
    """
    audit_log_id = f"audit_{uuid.uuid4().hex[:16]}"
    timestamp = datetime.utcnow().isoformat()
    
    try:
        item = {
            'audit_log_id': audit_log_id,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'timestamp': timestamp,
            'details': details or {},
            'ceo_id': ceo_id,
            'ip_address': ip_address
        }
        
        audit_logs_table.put_item(Item=item)
        
        logger.info(
            f"Audit event logged: {action}",
            extra={
                'audit_log_id': audit_log_id,
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )
        
        return audit_log_id
    
    except Exception as e:
        logger.error(
            f"Failed to log audit event: {str(e)}",
            extra={
                'user_id': user_id,
                'action': action,
                'resource_id': resource_id
            }
        )
        # Don't raise - audit logging failure shouldn't block the main operation
        return ""


def query_audit_logs(
    user_id: Optional[str] = None,
    ceo_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100
) -> list:
    """
    Query audit logs with filters.
    
    Args:
        user_id: Filter by user (optional)
        ceo_id: Filter by CEO for multi-tenancy (optional)
        action: Filter by action type (optional)
        resource_type: Filter by resource type (optional)
        limit: Max results to return
    
    Returns:
        List of audit log entries
    """
    try:
        # For now, scan with filters (in production, use GSI for efficient queries)
        scan_params = {'Limit': limit}
        filter_expressions = []
        expr_values = {}
        
        if user_id:
            filter_expressions.append('user_id = :user_id')
            expr_values[':user_id'] = user_id
        
        if ceo_id:
            filter_expressions.append('ceo_id = :ceo_id')
            expr_values[':ceo_id'] = ceo_id
        
        if action:
            filter_expressions.append('action = :action')
            expr_values[':action'] = action
        
        if resource_type:
            filter_expressions.append('resource_type = :resource_type')
            expr_values[':resource_type'] = resource_type
        
        if filter_expressions:
            scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_params['ExpressionAttributeValues'] = expr_values
        
        response = audit_logs_table.scan(**scan_params)
        logs = response.get('Items', [])
        
        # Sort by timestamp descending (most recent first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        logger.info(
            f"Retrieved {len(logs)} audit logs",
            extra={'filters': scan_params}
        )
        
        return logs
    
    except Exception as e:
        logger.error(f"Failed to query audit logs: {str(e)}")
        return []
