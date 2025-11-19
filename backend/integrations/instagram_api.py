"""
Instagram Messaging API Integration

Handles sending messages and OTPs via Instagram Direct Messages.

Meta Instagram Messaging API Documentation:
https://developers.facebook.com/docs/messenger-platform/instagram

Features:
- Send text messages via Instagram DM
- Send OTP securely
- Send interactive quick replies
- Template message support
- Error handling

Setup:
1. Connect Instagram Business Account to Facebook Page
2. Enable Instagram Messaging in Meta Business Manager
3. Generate Page Access Token (stored in Secrets Manager)
4. Set webhook URL for incoming messages
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from common.logger import logger
from common.config import settings


class InstagramAPI:
    """Instagram Messaging API client."""
    
    def __init__(self, access_token: str = None, page_id: str = None):
        """
        Initialize Instagram API client.
        
        Args:
            access_token: Meta Page Access Token
            page_id: Instagram-connected Facebook Page ID
        """
        self.access_token = access_token or getattr(settings, 'INSTAGRAM_ACCESS_TOKEN', None)
        self.page_id = page_id or getattr(settings, 'INSTAGRAM_PAGE_ID', None)
        self.base_url = "https://graph.facebook.com/v18.0/me/messages"
        
        if not self.access_token:
            logger.warning("Instagram access token not configured")
    
    async def send_message(
        self,
        to: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send text message via Instagram DM.
        
        Args:
            to: Recipient PSID (Page-Scoped ID) or Instagram IGID
            message: Message text (max 2000 characters)
        
        Returns:
            Dict with message ID and status
        
        Example:
            >>> await send_message("1234567890", "Hello from TrustGuard!")
            {"message_id": "mid.xxx", "status": "sent"}
        """
        # Remove 'ig_' prefix if present (from buyer_id)
        if to.startswith('ig_'):
            to = to[3:]
        
        payload = {
            "recipient": {
                "id": to
            },
            "message": {
                "text": message
            }
        }
        
        params = {
            "access_token": self.access_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get('message_id')
                    recipient_id = result.get('recipient_id')
                    
                    logger.info(
                        "Instagram message sent",
                        extra={
                            'to': to[-4:],  # Last 4 digits for privacy
                            'message_id': message_id,
                            'length': len(message)
                        }
                    )
                    
                    return {
                        'success': True,
                        'message_id': message_id,
                        'recipient_id': recipient_id,
                        'platform': 'instagram',
                        'to': to
                    }
                else:
                    error_data = response.json()
                    logger.error(
                        f"Instagram API error: {response.status_code}",
                        extra={'error': error_data}
                    )
                    return {
                        'success': False,
                        'error': error_data.get('error', {}).get('message', 'Unknown error'),
                        'platform': 'instagram'
                    }
        
        except Exception as e:
            logger.error(f"Instagram send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'instagram'
            }
    
    async def send_otp(
        self,
        to: str,
        otp: str,
        expires_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Send OTP to Instagram user with formatted message.
        
        Args:
            to: Recipient PSID
            otp: One-time password code
            expires_minutes: OTP expiration time
        
        Returns:
            Dict with send status
        """
        message = f"""🔐 TrustGuard Security Code

Your verification code is:

{otp}

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
            to: Recipient PSID
            buyer_name: Buyer's name (optional)
        
        Returns:
            Dict with send status
        """
        greeting = f"Hi {buyer_name}! 👋" if buyer_name else "Welcome! 👋"
        
        message = f"""{greeting}

Thank you for choosing TrustGuard! 🛡️

We're here to make your online shopping safe and secure.

How it works:
1️⃣ Browse products on Instagram
2️⃣ Place your order with the vendor
3️⃣ Get a verification code from us
4️⃣ Upload your payment receipt
5️⃣ We verify everything before delivery

Need help?
Just DM us anytime!

Reply 'verify <code>' to enter your OTP
Reply 'help' for more commands"""
        
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
            to: Recipient PSID
            order_id: Order reference
            amount: Order amount
            vendor_name: Vendor's business name
        
        Returns:
            Dict with send status
        """
        message = f"""✅ Order Confirmed

Order ID: {order_id}
Vendor: {vendor_name}
Amount: ₦{amount:,.2f}

Next Steps:
1. Make payment to vendor
2. Upload your payment receipt
3. Wait for verification
4. Delivery arranged ✈️

Reply 'upload' for receipt upload instructions

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
            to: Recipient PSID
            upload_url: Presigned S3 upload URL
            order_id: Order reference
        
        Returns:
            Dict with send status
        """
        message = f"""📸 Upload Your Receipt

Order: {order_id}

Instructions:
1. Take a clear photo of your payment receipt
2. Click the link below to upload
3. We'll verify and update your order

Upload Link:
{upload_url}

⏱ Link expires in 15 minutes

Tips for best results:
✓ Good lighting
✓ All text visible
✓ No blurry parts

Questions? DM us! 💬"""
        
        return await self.send_message(to, message)
    
    async def send_verification_complete(
        self,
        to: str,
        order_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Send verification result to buyer.
        
        Args:
            to: Recipient PSID
            order_id: Order reference
            status: 'approved' or 'rejected'
        
        Returns:
            Dict with send status
        """
        if status == 'approved':
            message = f"""✅ Payment Verified!

Order: {order_id}

Your payment has been confirmed! 🎉

The vendor has been notified and will proceed with delivery.

Track your order:
Reply 'order {order_id}' anytime

Thank you for trusting TrustGuard! 🛡️"""
        else:
            message = f"""⚠️ Verification Issue

Order: {order_id}

We couldn't verify your payment receipt. This could be due to:
• Unclear image quality
• Missing transaction details
• Bank information mismatch

What to do:
1. Contact your vendor
2. Upload a clearer receipt
3. DM us for assistance

Need help? We're here! 💬"""
        
        return await self.send_message(to, message)
    
    async def send_quick_replies(
        self,
        to: str,
        message_text: str,
        quick_replies: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send message with quick reply options.
        
        Args:
            to: Recipient PSID
            message_text: Message text
            quick_replies: List of quick reply options
                [{"content_type": "text", "title": "Option 1", "payload": "OPT1"}, ...]
        
        Returns:
            Dict with send status
        
        Note: Max 13 quick replies, title max 20 chars
        """
        # Remove 'ig_' prefix
        if to.startswith('ig_'):
            to = to[3:]
        
        # Format quick replies for Instagram API
        formatted_replies = [
            {
                "content_type": qr.get("content_type", "text"),
                "title": qr["title"][:20],  # Max 20 chars
                "payload": qr.get("payload", qr["title"])
            }
            for qr in quick_replies[:13]  # Max 13 quick replies
        ]
        
        payload = {
            "recipient": {
                "id": to
            },
            "message": {
                "text": message_text,
                "quick_replies": formatted_replies
            }
        }
        
        params = {
            "access_token": self.access_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get('message_id')
                    
                    logger.info("Instagram quick replies sent", extra={'to': to[-4:]})
                    
                    return {
                        'success': True,
                        'message_id': message_id,
                        'platform': 'instagram'
                    }
                else:
                    error_data = response.json()
                    logger.error(f"Instagram quick replies error: {response.status_code}", extra={'error': error_data})
                    return {'success': False, 'error': error_data}
        
        except Exception as e:
            logger.error(f"Instagram quick replies send failed: {str(e)}")
            return {'success': False, 'error': str(e)}


# Singleton instance
instagram_api = InstagramAPI()
