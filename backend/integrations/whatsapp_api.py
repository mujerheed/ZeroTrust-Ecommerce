"""
WhatsApp Business API Integration

Handles sending messages and OTPs via WhatsApp Cloud API.

Meta WhatsApp Cloud API Documentation:
https://developers.facebook.com/docs/whatsapp/cloud-api

Features:
- Send text messages
- Send OTP with formatting
- Send interactive buttons
- Template messages support
- Error handling and retries

Setup:
1. Create Meta Business Account
2. Get WhatsApp Business API access
3. Set up business phone number
4. Generate access token (stored in Secrets Manager)
5. Set webhook URL for incoming messages
"""

import httpx
import json
from typing import Dict, Any, Optional
from common.logger import logger
from common.config import settings


class WhatsAppAPI:
    """WhatsApp Business Cloud API client."""
    
    def __init__(self, access_token: str = None, phone_number_id: str = None):
        """
        Initialize WhatsApp API client.
        
        Args:
            access_token: Meta access token (from Secrets Manager or .env)
            phone_number_id: WhatsApp Business Phone Number ID
        """
        self.access_token = access_token or getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        self.phone_number_id = phone_number_id or getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        if not self.access_token:
            logger.warning("WhatsApp access token not configured")
        if not self.phone_number_id:
            logger.warning("WhatsApp phone number ID not configured")
    
    async def send_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Send text message to WhatsApp user.
        
        Args:
            to: Recipient WhatsApp ID (phone number with country code, no +)
            message: Message text (max 4096 characters)
            preview_url: Enable link preview
        
        Returns:
            Dict with message ID and status
        
        Example:
            >>> await send_message("2348012345678", "Hello from TrustGuard!")
            {"message_id": "wamid.xxx", "status": "sent"}
        """
        # Remove 'wa_' prefix if present (from buyer_id)
        if to.startswith('wa_'):
            to = to[3:]
        
        # Ensure no + prefix (Meta expects plain number)
        to = to.lstrip('+')
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get('messages', [{}])[0].get('id')
                    
                    logger.info(
                        "WhatsApp message sent",
                        extra={
                            'to': to[-4:],  # Last 4 digits for privacy
                            'message_id': message_id,
                            'length': len(message)
                        }
                    )
                    
                    return {
                        'success': True,
                        'message_id': message_id,
                        'platform': 'whatsapp',
                        'to': to
                    }
                else:
                    error_data = response.json()
                    logger.error(
                        f"WhatsApp API error: {response.status_code}",
                        extra={'error': error_data}
                    )
                    return {
                        'success': False,
                        'error': error_data.get('error', {}).get('message', 'Unknown error'),
                        'platform': 'whatsapp'
                    }
        
        except Exception as e:
            logger.error(f"WhatsApp send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'whatsapp'
            }
    
    async def send_otp(
        self,
        to: str,
        otp: str,
        expires_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Send OTP to WhatsApp user with formatted message.
        
        Args:
            to: Recipient WhatsApp ID
            otp: One-time password code
            expires_minutes: OTP expiration time
        
        Returns:
            Dict with send status
        """
        message = f"""🔐 *TrustGuard Security Code*

Your verification code is:

*{otp}*

⏱ Valid for {expires_minutes} minutes
🚫 Do not share this code with anyone

This code is for order verification only."""
        
        return await self.send_message(to, message)
    
    async def send_welcome_message(
        self,
        to: str,
        buyer_name: str = None
    ) -> Dict[str, Any]:
        """
        Send welcome message to new buyer.
        
        Args:
            to: Recipient WhatsApp ID
            buyer_name: Buyer's name (optional)
        
        Returns:
            Dict with send status
        """
        greeting = f"Hi {buyer_name}! 👋" if buyer_name else "Welcome! 👋"
        
        message = f"""{greeting}

Thank you for choosing TrustGuard! 🛡️

We're here to make your online shopping *safe and secure*.

*How it works:*
1️⃣ Browse products on Instagram/WhatsApp
2️⃣ Place your order with the vendor
3️⃣ Get a verification code from us
4️⃣ Upload your payment receipt
5️⃣ We verify everything before delivery

*Need help?*
Just message us anytime!

Type *verify <code>* to enter your OTP
Type *help* for more commands"""
        
        return await self.send_message(to, message)
    
    async def send_order_confirmation(
        self,
        to: str,
        order_id: str,
        amount: float,
        vendor_name: str
    ) -> Dict[str, Any]:
        """
        Send order confirmation to buyer.
        
        Args:
            to: Recipient WhatsApp ID
            order_id: Order reference
            amount: Order amount
            vendor_name: Vendor's business name
        
        Returns:
            Dict with send status
        """
        message = f"""✅ *Order Confirmed*

*Order ID:* {order_id}
*Vendor:* {vendor_name}
*Amount:* ₦{amount:,.2f}

*Next Steps:*
1. Make payment to vendor
2. Upload your payment receipt
3. Wait for verification
4. Delivery arranged ✈️

Type *upload* for receipt upload instructions

Need help? Just ask! 💬"""
        
        return await self.send_message(to, message)
    
    async def send_receipt_upload_instructions(
        self,
        to: str,
        upload_url: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Send receipt upload instructions with link.
        
        Args:
            to: Recipient WhatsApp ID
            upload_url: Presigned S3 upload URL
            order_id: Order reference
        
        Returns:
            Dict with send status
        """
        message = f"""📸 *Upload Your Receipt*

*Order:* {order_id}

*Instructions:*
1. Take a clear photo of your payment receipt
2. Click the link below to upload
3. We'll verify and update your order

*Upload Link:*
{upload_url}

⏱ Link expires in 15 minutes

*Tips for best results:*
✓ Good lighting
✓ All text visible
✓ No blurry parts

Questions? Message us! 💬"""
        
        return await self.send_message(to, message, preview_url=True)
    
    async def send_verification_complete(
        self,
        to: str,
        order_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Send verification result to buyer.
        
        Args:
            to: Recipient WhatsApp ID
            order_id: Order reference
            status: 'approved' or 'rejected'
        
        Returns:
            Dict with send status
        """
        if status == 'approved':
            message = f"""✅ *Payment Verified!*

*Order:* {order_id}

Your payment has been confirmed! 🎉

The vendor has been notified and will proceed with delivery.

*Track your order:*
Type *order {order_id}* anytime

Thank you for trusting TrustGuard! 🛡️"""
        else:
            message = f"""⚠️ *Verification Issue*

*Order:* {order_id}

We couldn't verify your payment receipt. This could be due to:
• Unclear image quality
• Missing transaction details
• Bank information mismatch

*What to do:*
1. Contact your vendor
2. Upload a clearer receipt
3. Message us for assistance

Need help? We're here! 💬"""
        
        return await self.send_message(to, message)
    
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send message with interactive reply buttons.
        
        Args:
            to: Recipient WhatsApp ID
            body_text: Message text
            buttons: List of button dicts [{"id": "btn1", "title": "Option 1"}, ...]
        
        Returns:
            Dict with send status
        
        Note: Max 3 buttons, title max 20 chars
        """
        # Remove 'wa_' prefix
        if to.startswith('wa_'):
            to = to[3:]
        to = to.lstrip('+')
        
        # Format buttons for WhatsApp API
        button_components = [
            {
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"][:20]  # Max 20 chars
                }
            }
            for btn in buttons[:3]  # Max 3 buttons
        ]
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": button_components
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get('messages', [{}])[0].get('id')
                    
                    logger.info("WhatsApp interactive message sent", extra={'to': to[-4:]})
                    
                    return {
                        'success': True,
                        'message_id': message_id,
                        'platform': 'whatsapp'
                    }
                else:
                    error_data = response.json()
                    logger.error(f"WhatsApp interactive error: {response.status_code}", extra={'error': error_data})
                    return {'success': False, 'error': error_data}
        
        except Exception as e:
            logger.error(f"WhatsApp interactive send failed: {str(e)}")
            return {'success': False, 'error': str(e)}


# Singleton instance
whatsapp_api = WhatsAppAPI()
