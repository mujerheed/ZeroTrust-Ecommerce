"""
Lambda function for scheduled Meta OAuth token refresh.

Runs daily at 2 AM UTC via EventBridge.
Checks all CEO tokens and refreshes if expiring soon (< 7 days).
"""

import json
from typing import Dict, Any, List
from common.logger import logger
from integrations.token_utils import (
    get_meta_token_info,
    calculate_days_until_expiry,
    refresh_meta_token,
    update_secrets_manager,
    publish_token_expiry_metric
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Scheduled token refresh for all CEOs.
    
    Triggered by EventBridge daily at 2 AM UTC.
    
    Args:
        event: EventBridge event
        context: Lambda context
    
    Returns:
        Dict with refresh results for all CEOs
    """
    logger.info("Starting scheduled token refresh check")
    
    results = []
    
    try:
        # Get all CEOs
        ceos = get_all_ceos()
        logger.info(f"Found {len(ceos)} CEOs to check")
        
        for ceo in ceos:
            ceo_id = ceo.get('ceo_id')
            
            try:
                # Check and refresh tokens for this CEO
                ceo_result = check_and_refresh_ceo_tokens(ceo_id)
                results.append(ceo_result)
            
            except Exception as e:
                logger.error(f"Failed to process CEO {ceo_id}: {str(e)}", exc_info=True)
                send_failure_notification(ceo_id, str(e))
                results.append({
                    'ceo_id': ceo_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Summary
        success_count = sum(1 for r in results if r['status'] in ['ok', 'refreshed'])
        error_count = sum(1 for r in results if r['status'] == 'error')
        
        logger.info(f"Token refresh complete: {success_count} success, {error_count} errors")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Token refresh complete',
                'total_ceos': len(ceos),
                'success': success_count,
                'errors': error_count,
                'results': results
            })
        }
    
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def check_and_refresh_ceo_tokens(ceo_id: str) -> Dict[str, Any]:
    """
    Check and refresh tokens for a single CEO.
    
    Args:
        ceo_id: CEO ID
    
    Returns:
        Dict with refresh status
    """
    logger.info(f"Checking tokens for CEO {ceo_id}")
    
    # Get token info
    token_info = get_meta_token_info(ceo_id)
    
    results = {
        'ceo_id': ceo_id,
        'whatsapp': None,
        'instagram': None,
        'status': 'ok'
    }
    
    # Check WhatsApp token
    if token_info['whatsapp']['access_token']:
        wa_days = calculate_days_until_expiry(token_info['whatsapp']['expires_at'])
        publish_token_expiry_metric(ceo_id, 'whatsapp', wa_days)
        
        logger.info(f"WhatsApp token for {ceo_id}: {wa_days} days remaining")
        
        if wa_days < 7:
            logger.warning(f"WhatsApp token expiring soon for {ceo_id}, refreshing...")
            try:
                new_token = refresh_meta_token(token_info['whatsapp']['access_token'])
                update_secrets_manager(ceo_id, 'whatsapp', new_token)
                send_success_notification(ceo_id, 'whatsapp', wa_days)
                results['whatsapp'] = {'status': 'refreshed', 'days_remaining': wa_days}
                results['status'] = 'refreshed'
            except Exception as e:
                logger.error(f"Failed to refresh WhatsApp token: {str(e)}")
                results['whatsapp'] = {'status': 'error', 'error': str(e)}
                results['status'] = 'error'
                raise
        else:
            results['whatsapp'] = {'status': 'ok', 'days_remaining': wa_days}
    
    # Check Instagram token
    if token_info['instagram']['access_token']:
        ig_days = calculate_days_until_expiry(token_info['instagram']['expires_at'])
        publish_token_expiry_metric(ceo_id, 'instagram', ig_days)
        
        logger.info(f"Instagram token for {ceo_id}: {ig_days} days remaining")
        
        if ig_days < 7:
            logger.warning(f"Instagram token expiring soon for {ceo_id}, refreshing...")
            try:
                new_token = refresh_meta_token(token_info['instagram']['access_token'])
                update_secrets_manager(ceo_id, 'instagram', new_token)
                send_success_notification(ceo_id, 'instagram', ig_days)
                results['instagram'] = {'status': 'refreshed', 'days_remaining': ig_days}
                results['status'] = 'refreshed'
            except Exception as e:
                logger.error(f"Failed to refresh Instagram token: {str(e)}")
                results['instagram'] = {'status': 'error', 'error': str(e)}
                results['status'] = 'error'
                raise
        else:
            results['instagram'] = {'status': 'ok', 'days_remaining': ig_days}
    
    return results


def get_all_ceos() -> List[Dict[str, Any]]:
    """
    Get all CEOs from database.
    
    Returns:
        List of CEO records
    """
    try:
        from ceo_service.database import USERS_TABLE
        
        response = USERS_TABLE.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'CEO'}
        )
        
        ceos = response.get('Items', [])
        logger.info(f"Retrieved {len(ceos)} CEOs from database")
        
        return ceos
    
    except Exception as e:
        logger.error(f"Failed to get CEOs: {str(e)}")
        raise


def send_success_notification(ceo_id: str, platform: str, days_remaining: int) -> None:
    """
    Send SNS notification on successful token refresh.
    
    Args:
        ceo_id: CEO ID
        platform: 'whatsapp' or 'instagram'
        days_remaining: Days that were remaining before refresh
    """
    try:
        import boto3
        import os
        
        topic_arn = os.getenv('MONITORING_ALERT_TOPIC_ARN')
        if not topic_arn:
            logger.warning("MONITORING_ALERT_TOPIC_ARN not configured, skipping notification")
            return
        
        sns = boto3.client('sns')
        
        message = f"""
TrustGuard Token Refresh Success

CEO ID: {ceo_id}
Platform: {platform.upper()}
Days Remaining: {days_remaining}
Action: Token refreshed successfully
New Expiry: 60 days from now

This is an automated notification from the TrustGuard token refresh scheduler.
"""
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"✅ Token Refreshed: {platform.upper()} ({ceo_id})",
            Message=message
        )
        
        logger.info(f"Sent success notification for {platform} token refresh")
    
    except Exception as e:
        logger.warning(f"Failed to send success notification: {str(e)}")
        # Don't raise - notification failure shouldn't block token refresh


def send_failure_notification(ceo_id: str, error: str) -> None:
    """
    Send SNS notification on token refresh failure.
    
    Args:
        ceo_id: CEO ID
        error: Error message
    """
    try:
        import boto3
        import os
        
        topic_arn = os.getenv('MONITORING_ALERT_TOPIC_ARN')
        if not topic_arn:
            logger.warning("MONITORING_ALERT_TOPIC_ARN not configured, skipping notification")
            return
        
        sns = boto3.client('sns')
        
        message = f"""
🚨 TrustGuard Token Refresh FAILED

CEO ID: {ceo_id}
Error: {error}

Action Required: Manual intervention needed to refresh Meta OAuth tokens.

Check CloudWatch logs for details:
/aws/lambda/TrustGuard-TokenRefresh-dev

This is an automated alert from the TrustGuard token refresh scheduler.
"""
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"🚨 Token Refresh Failed: {ceo_id}",
            Message=message
        )
        
        logger.info(f"Sent failure notification for CEO {ceo_id}")
    
    except Exception as e:
        logger.warning(f"Failed to send failure notification: {str(e)}")
