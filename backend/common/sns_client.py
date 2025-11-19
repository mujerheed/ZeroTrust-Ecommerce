"""
SNS Notification Client

Handles CEO alert notifications for high-value escalations.
Zero Trust: All notifications logged, PII masked in logs.
"""

import json
from typing import Dict, Any, Optional
from common.config import settings
from common.db_connection import sns_client
from common.logger import logger


def send_escalation_alert(
    ceo_id: str,
    escalation_id: str,
    order_id: str,
    amount: float,
    reason: str,
    vendor_name: Optional[str] = None,
    buyer_masked_phone: Optional[str] = None
) -> bool:
    """
    Send escalation notification to CEO via SNS (SMS + Email).
    
    Args:
        ceo_id (str): CEO identifier
        escalation_id (str): Escalation identifier
        order_id (str): Order identifier
        amount (float): Order amount in Naira
        reason (str): Escalation reason
        vendor_name (str, optional): Vendor display name
        buyer_masked_phone (str, optional): Masked buyer phone (last 4 digits)
    
    Returns:
        bool: True if notification sent successfully
    """
    if not settings.ESCALATION_SNS_TOPIC_ARN:
        logger.warning("ESCALATION_SNS_TOPIC_ARN not configured, skipping alert")
        return False
    
    # Format amount with thousand separators
    formatted_amount = f"₦{amount:,.2f}"
    
    # Build message
    subject = f"TrustGuard Escalation Alert: {formatted_amount}"
    
    message_lines = [
        f"⚠️ HIGH-VALUE TRANSACTION ALERT",
        f"",
        f"Escalation ID: {escalation_id}",
        f"Order ID: {order_id}",
        f"Amount: {formatted_amount}",
        f"Reason: {_format_reason(reason)}",
    ]
    
    if vendor_name:
        message_lines.append(f"Vendor: {vendor_name}")
    
    if buyer_masked_phone:
        message_lines.append(f"Buyer: ***{buyer_masked_phone}")
    
    message_lines.extend([
        f"",
        f"Action Required:",
        f"1. Log in to TrustGuard CEO Dashboard",
        f"2. Review transaction details",
        f"3. Enter OTP to approve/reject",
        f"",
        f"⏱️ Escalation expires in 24 hours"
    ])
    
    message = "\n".join(message_lines)
    
    # SNS message with attributes for filtering
    try:
        response = sns_client.publish(
            TopicArn=settings.ESCALATION_SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'ceo_id': {
                    'DataType': 'String',
                    'StringValue': ceo_id
                },
                'escalation_id': {
                    'DataType': 'String',
                    'StringValue': escalation_id
                },
                'amount': {
                    'DataType': 'Number',
                    'StringValue': str(int(amount))
                },
                'reason': {
                    'DataType': 'String',
                    'StringValue': reason
                }
            }
        )
        
        message_id = response.get('MessageId')
        logger.info(
            f"Escalation alert sent: {escalation_id} to CEO {ceo_id}, "
            f"SNS MessageId={message_id}, amount={formatted_amount}"
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send escalation alert {escalation_id} to CEO {ceo_id}: {str(e)}"
        )
        return False


def send_escalation_resolved_notification(
    ceo_id: str,
    escalation_id: str,
    order_id: str,
    decision: str,
    amount: float
) -> bool:
    """
    Notify stakeholders that escalation was resolved.
    
    Args:
        ceo_id (str): CEO identifier
        escalation_id (str): Escalation identifier
        order_id (str): Order identifier
        decision (str): 'APPROVED' or 'REJECTED'
        amount (float): Order amount in Naira
    
    Returns:
        bool: True if notification sent successfully
    """
    if not settings.ESCALATION_SNS_TOPIC_ARN:
        return False
    
    formatted_amount = f"₦{amount:,.2f}"
    decision_emoji = "✅" if decision == "APPROVED" else "❌"
    action_text = "continue" if decision == "APPROVED" else "be canceled"
    
    subject = f"TrustGuard: Escalation {decision}"
    message = (
        f"{decision_emoji} Escalation {decision}\n"
        f"\n"
        f"Escalation ID: {escalation_id}\n"
        f"Order ID: {order_id}\n"
        f"Amount: {formatted_amount}\n"
        f"Decision: {decision}\n"
        f"\n"
        f"Order processing will {action_text}."
    )
    
    try:
        response = sns_client.publish(
            TopicArn=settings.ESCALATION_SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'ceo_id': {
                    'DataType': 'String',
                    'StringValue': ceo_id
                },
                'escalation_id': {
                    'DataType': 'String',
                    'StringValue': escalation_id
                },
                'decision': {
                    'DataType': 'String',
                    'StringValue': decision
                }
            }
        )
        
        logger.info(
            f"Escalation resolved notification sent: {escalation_id}, "
            f"decision={decision}, MessageId={response.get('MessageId')}"
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send escalation resolved notification {escalation_id}: {str(e)}"
        )
        return False


def _format_reason(reason: str) -> str:
    """Format escalation reason for human readability."""
    reason_map = {
        'HIGH_VALUE': 'High-Value Transaction (≥ ₦1,000,000)',
        'VENDOR_FLAGGED': 'Vendor Flagged Receipt',
        'TEXTRACT_LOW_CONFIDENCE': 'Low OCR Confidence Score'
    }
    return reason_map.get(reason, reason)


def send_buyer_notification(
    buyer_phone: str,
    order_id: str,
    status: str,
    additional_message: Optional[str] = None
) -> bool:
    """
    Send order status notification to buyer via SMS.
    
    Args:
        buyer_phone (str): Buyer's phone number (Nigerian format)
        order_id (str): Order identifier
        status (str): Order status message
        additional_message (str, optional): Extra context
    
    Returns:
        bool: True if SMS sent successfully
    """
    # Ensure phone is in E.164 format for SMS
    if buyer_phone.startswith('0'):
        buyer_phone = '+234' + buyer_phone[1:]
    elif buyer_phone.startswith('234'):
        buyer_phone = '+' + buyer_phone
    elif not buyer_phone.startswith('+'):
        buyer_phone = '+234' + buyer_phone
    
    message = f"TrustGuard Order Update\n\nOrder ID: {order_id}\nStatus: {status}"
    
    if additional_message:
        message += f"\n\n{additional_message}"
    
    try:
        response = sns_client.publish(
            PhoneNumber=buyer_phone,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': 'TrustGuard'
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        
        # Log with masked phone
        masked_phone = buyer_phone[-4:] if len(buyer_phone) >= 4 else "****"
        logger.info(
            f"Buyer notification sent: Order {order_id} to ***{masked_phone}, "
            f"MessageId={response.get('MessageId')}"
        )
        return True
        
    except Exception as e:
        masked_phone = buyer_phone[-4:] if len(buyer_phone) >= 4 else "****"
        logger.error(
            f"Failed to send buyer notification for order {order_id} to ***{masked_phone}: {str(e)}"
        )
        return False
