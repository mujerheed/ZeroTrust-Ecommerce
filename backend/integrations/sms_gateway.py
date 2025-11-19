"""
SMS Gateway Service (AWS SNS)

Provides SMS fallback when WhatsApp/Instagram delivery fails.
Uses AWS SNS for reliable SMS delivery.

Use Cases:
- Platform API unavailable
- User doesn't have WhatsApp/Instagram
- Emergency OTP delivery
- Backup communication channel

Features:
- Nigerian phone number validation
- AWS SNS integration
- Delivery status tracking
- Cost-effective SMS routing
"""

import boto3
import re
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from common.logger import logger
from common.config import settings


class SMSGateway:
    """AWS SNS SMS delivery service."""
    
    def __init__(self):
        """Initialize AWS SNS client."""
        self.sns_client = boto3.client(
            'sns',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'TrustGuard')
    
    def validate_nigerian_phone(self, phone: str) -> Optional[str]:
        """
        Validate and format Nigerian phone number.
        
        Accepts:
        - +2348012345678 (international format)
        - 2348012345678 (without +)
        - 08012345678 (local format)
        
        Returns:
        - +2348012345678 (E.164 format)
        
        Args:
            phone: Phone number in various formats
        
        Returns:
            Formatted phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove spaces, hyphens, parentheses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Remove wa_ prefix if present
        if phone.startswith('wa_'):
            phone = phone[3:]
        
        # Remove + if present
        phone = phone.lstrip('+')
        
        # Convert local 0 prefix to 234
        if phone.startswith('0') and len(phone) == 11:
            phone = '234' + phone[1:]
        
        # Ensure 234 prefix
        if not phone.startswith('234'):
            if len(phone) == 10:  # Assume Nigerian number
                phone = '234' + phone
            else:
                logger.warning(f"Invalid phone format: {phone}")
                return None
        
        # Validate length (234 + 10 digits = 13)
        if len(phone) != 13:
            logger.warning(f"Invalid phone length: {phone}")
            return None
        
        # Validate it's all digits
        if not phone.isdigit():
            logger.warning(f"Phone contains non-digits: {phone}")
            return None
        
        # Return in E.164 format
        return '+' + phone
    
    async def send_sms(
        self,
        to: str,
        message: str,
        message_type: str = 'Transactional'
    ) -> Dict[str, Any]:
        """
        Send SMS via AWS SNS.
        
        Args:
            to: Recipient phone number (Nigerian format)
            message: SMS text (max 160 chars for single SMS)
            message_type: 'Transactional' or 'Promotional'
        
        Returns:
            Dict with message ID and status
        
        Example:
            >>> await send_sms("+2348012345678", "Your OTP is 12345678")
            {"success": True, "message_id": "xxx", "platform": "sms"}
        """
        # Validate and format phone number
        formatted_phone = self.validate_nigerian_phone(to)
        
        if not formatted_phone:
            logger.error(f"Invalid phone number for SMS: {to}")
            return {
                'success': False,
                'error': 'Invalid phone number format',
                'platform': 'sms'
            }
        
        try:
            # Send SMS via SNS
            response = self.sns_client.publish(
                PhoneNumber=formatted_phone,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': self.sender_id
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': message_type  # Transactional or Promotional
                    }
                }
            )
            
            message_id = response.get('MessageId')
            
            logger.info(
                "SMS sent successfully",
                extra={
                    'to': formatted_phone[-4:],  # Last 4 digits for privacy
                    'message_id': message_id,
                    'length': len(message),
                    'type': message_type
                }
            )
            
            return {
                'success': True,
                'message_id': message_id,
                'platform': 'sms',
                'to': formatted_phone,
                'length': len(message)
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(
                f"AWS SNS error: {error_code}",
                extra={
                    'error': error_message,
                    'to': formatted_phone[-4:] if formatted_phone else 'unknown'
                }
            )
            
            return {
                'success': False,
                'error': f"{error_code}: {error_message}",
                'platform': 'sms'
            }
        
        except Exception as e:
            logger.error(f"SMS send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'sms'
            }
    
    async def send_otp(
        self,
        to: str,
        otp: str,
        expires_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Send OTP via SMS.
        
        Args:
            to: Recipient phone number
            otp: One-time password code
            expires_minutes: OTP expiration time
        
        Returns:
            Dict with send status
        """
        message = f"""TrustGuard Security Code

Your verification code is: {otp}

Valid for {expires_minutes} minutes.
Do not share this code.

Order verification only."""
        
        return await self.send_sms(to, message, message_type='Transactional')
    
    async def send_with_fallback(
        self,
        to: str,
        message: str,
        platform_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send SMS as fallback if platform delivery failed.
        
        Args:
            to: Recipient phone (for SMS) or buyer_id (extract phone)
            message: Message text
            platform_result: Result from WhatsApp/Instagram attempt
        
        Returns:
            Dict with final delivery status
        """
        # Check if platform delivery was successful
        if platform_result.get('success'):
            logger.info("Platform delivery successful, no SMS fallback needed")
            return platform_result
        
        # Platform failed, try SMS
        logger.warning(
            f"Platform delivery failed: {platform_result.get('error')}, trying SMS fallback"
        )
        
        # Extract phone number from buyer_id if needed
        phone = to
        if to.startswith('wa_'):
            phone = to[3:]  # Remove wa_ prefix
        
        # Send via SMS
        sms_result = await self.send_sms(phone, message)
        
        if sms_result.get('success'):
            logger.info("SMS fallback successful")
            return {
                **sms_result,
                'fallback': True,
                'original_platform': platform_result.get('platform'),
                'original_error': platform_result.get('error')
            }
        else:
            logger.error("Both platform and SMS delivery failed")
            return {
                'success': False,
                'platform_error': platform_result.get('error'),
                'sms_error': sms_result.get('error'),
                'delivery_failed': True
            }


# Singleton instance
sms_gateway = SMSGateway()
