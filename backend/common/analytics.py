"""
Analytics and time-series data aggregation for TrustGuard dashboards.

This module provides chart data for:
- Vendor: Daily order counts
- CEO: Fraud flag trends, vendor performance metrics
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from common.db_connection import dynamodb
from common.config import settings
from common.logger import logger


ORDERS_TABLE = dynamodb.Table(settings.ORDERS_TABLE)
AUDIT_LOGS_TABLE = dynamodb.Table(settings.AUDIT_LOGS_TABLE)


def get_vendor_orders_by_day(vendor_id: str, days: int = 7) -> List[Dict]:
    """
    Get daily order counts for a vendor over the past N days.
    
    Args:
        vendor_id: Vendor identifier
        days: Number of days to look back (default 7)
    
    Returns:
        List of dict with date and count:
        [
            {"date": "2025-11-13", "count": 5},
            {"date": "2025-11-14", "count": 8},
            ...
        ]
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    start_timestamp = int(start_date.timestamp())
    
    # Query orders for this vendor
    try:
        response = ORDERS_TABLE.query(
            IndexName="VendorIndex",
            KeyConditionExpression="vendor_id = :vendor_id",
            FilterExpression="created_at >= :start_ts",
            ExpressionAttributeValues={
                ":vendor_id": vendor_id,
                ":start_ts": start_timestamp
            }
        )
        
        orders = response.get("Items", [])
        
        # Group orders by date
        daily_counts = defaultdict(int)
        for order in orders:
            created_at = order.get("created_at", 0)
            order_date = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d")
            daily_counts[order_date] += 1
        
        # Fill in missing dates with 0 counts
        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            result.append({
                "date": date_str,
                "count": daily_counts.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        logger.info(f"Vendor orders by day retrieved", extra={
            "vendor_id": vendor_id,
            "days": days,
            "total_orders": len(orders)
        })
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get vendor orders by day: {str(e)}", extra={"vendor_id": vendor_id})
        return []


def get_ceo_fraud_trends(ceo_id: str, days: int = 7) -> List[Dict]:
    """
    Get daily fraud flag counts for a CEO's business over the past N days.
    
    Args:
        ceo_id: CEO identifier
        days: Number of days to look back (default 7)
    
    Returns:
        List of dict with date and fraud_count:
        [
            {"date": "2025-11-13", "fraud_count": 2},
            {"date": "2025-11-14", "fraud_count": 0},
            ...
        ]
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    start_timestamp = int(start_date.timestamp())
    
    # Fraud-related actions
    fraud_actions = ["ORDER_FLAGGED", "RECEIPT_FLAGGED", "ESCALATION_CREATED", "FRAUD_DETECTED"]
    
    # Query audit logs for fraud events
    try:
        response = AUDIT_LOGS_TABLE.scan(
            FilterExpression="ceo_id = :ceo_id AND #ts >= :start_ts",
            ExpressionAttributeNames={"#ts": "timestamp"},
            ExpressionAttributeValues={
                ":ceo_id": ceo_id,
                ":start_ts": start_timestamp
            }
        )
        
        all_logs = response.get("Items", [])
        fraud_logs = [log for log in all_logs if log.get("action") in fraud_actions]
        
        # Group fraud events by date
        daily_fraud_counts = defaultdict(int)
        for log in fraud_logs:
            log_timestamp = log.get("timestamp", 0)
            log_date = datetime.fromtimestamp(log_timestamp).strftime("%Y-%m-%d")
            daily_fraud_counts[log_date] += 1
        
        # Fill in missing dates with 0 counts
        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            result.append({
                "date": date_str,
                "fraud_count": daily_fraud_counts.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        logger.info(f"CEO fraud trends retrieved", extra={
            "ceo_id": ceo_id,
            "days": days,
            "total_fraud_events": len(fraud_logs)
        })
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get fraud trends: {str(e)}", extra={"ceo_id": ceo_id})
        return []


def get_vendor_performance_summary(ceo_id: str) -> List[Dict]:
    """
    Get performance summary for all vendors under a CEO.
    
    Args:
        ceo_id: CEO identifier
    
    Returns:
        List of vendor performance metrics:
        [
            {
                "vendor_id": "vendor_123",
                "vendor_name": "Ada's Fashion",
                "total_orders": 42,
                "flag_rate": 0.024,  # 2.4%
                "avg_approval_time_minutes": 18
            },
            ...
        ]
    """
    from ceo_service.database import get_all_vendors_for_ceo, get_orders_for_ceo, get_audit_logs
    
    vendors = get_all_vendors_for_ceo(ceo_id)
    performance_data = []
    
    for vendor in vendors:
        vendor_id = vendor.get("user_id")
        vendor_name = vendor.get("name", "Unknown")
        
        # Get all orders for this vendor
        vendor_orders = get_orders_for_ceo(ceo_id=ceo_id, vendor_id=vendor_id)
        total_orders = len(vendor_orders)
        
        if total_orders == 0:
            # No orders yet
            performance_data.append({
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
                "total_orders": 0,
                "flag_rate": 0.0,
                "avg_approval_time_minutes": 0
            })
            continue
        
        # Count flagged orders
        fraud_actions = ["ORDER_FLAGGED", "RECEIPT_FLAGGED"]
        vendor_logs = get_audit_logs(ceo_id=ceo_id, user_id=vendor_id, limit=1000)
        flagged_count = len([log for log in vendor_logs if log.get("action") in fraud_actions])
        flag_rate = flagged_count / total_orders if total_orders > 0 else 0.0
        
        # Calculate average approval time
        approval_times = []
        for order in vendor_orders:
            created_at = order.get("created_at", 0)
            updated_at = order.get("updated_at", 0)
            if updated_at > created_at and order.get("order_status") in ["verified", "APPROVED"]:
                approval_time_seconds = updated_at - created_at
                approval_times.append(approval_time_seconds / 60)  # Convert to minutes
        
        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
        
        performance_data.append({
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "total_orders": total_orders,
            "flag_rate": round(flag_rate, 3),
            "avg_approval_time_minutes": round(avg_approval_time, 1)
        })
    
    logger.info(f"Vendor performance summary generated", extra={
        "ceo_id": ceo_id,
        "vendor_count": len(vendors)
    })
    
    return performance_data
