"""
Chatbot Message Router

Routes incoming messages from WhatsApp/Instagram to appropriate handlers
based on intent detection and conversation context.

Intent Categories:
- Registration: "register", "start", "hi", "hello"
- OTP Verification: "verify <code>", "<8-digit code>"
- Order Status: "order <order_id>", "status"
- Receipt Upload: "upload", "receipt"
- Help: "help", "?"

Features:
- Natural language intent detection
- Multi-platform support (WhatsApp/Instagram)
- Multi-CEO tenancy
- Context-aware responses
- Session management
"""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from common.logger import logger
from auth_service.database import create_buyer, get_buyer_by_id
from auth_service.otp_manager import generate_otp, verify_otp, store_otp
from integrations.whatsapp_api import whatsapp_api
from integrations.instagram_api import instagram_api


class ChatbotRouter:
    """Routes and processes chatbot messages."""
    
    # Intent patterns
    INTENT_PATTERNS = {
        'register': r'(?i)^(register|start|hi|hello|hey|begin)$',
        'verify_otp': r'(?i)^verify\s+([a-zA-Z0-9!@#$%^&*]{6,8})$',
        'otp_only': r'^([a-zA-Z0-9!@#$%^&*]{8})$',  # Direct 8-char OTP input
        'order_status': r'(?i)^(?:order|status)\s+(\S+)$',
        'upload': r'(?i)^(?:upload|receipt)$',
        'help': r'(?i)^(?:help|\?)$'
    }
    
    def __init__(self):
        self.whatsapp = whatsapp_api
        self.instagram = instagram_api
    
    def detect_intent(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Detect user intent from message text.
        
        Args:
            text: Message text
        
        Returns:
            Tuple of (intent, extracted_value)
            e.g., ('verify_otp', 'ABC12345') or ('help', None)
        """
        if not text:
            return ('unknown', None)
        
        text = text.strip()
        
        # Check each intent pattern
        for intent, pattern in self.INTENT_PATTERNS.items():
            match = re.match(pattern, text)
            if match:
                # Extract captured group if exists
                value = match.group(1) if match.groups() else None
                return (intent, value)
        
        # Default
        return ('unknown', None)
    
    async def route_message(
        self,
        parsed_message: Dict[str, Any],
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Route message to appropriate handler based on intent.
        
        Args:
            parsed_message: Parsed message dict from webhook_handler
            ceo_id: CEO ID for multi-tenancy
        
        Returns:
            Dict with response and action taken
        """
        sender_id = parsed_message['sender_id']
        text = parsed_message.get('text', '').strip()
        platform = parsed_message['platform']
        
        logger.info(
            f"Routing message from {platform}",
            extra={
                'sender': sender_id,
                'text_preview': text[:50] if text else None,
                'ceo_id': ceo_id
            }
        )
        
        # Detect intent
        intent, value = self.detect_intent(text)
        
        logger.debug(f"Detected intent: {intent}, value: {value}")
        
        # Route to handler
        if intent == 'register':
            return await self.handle_registration(sender_id, platform, ceo_id, parsed_message)
        
        elif intent == 'verify_otp':
            return await self.handle_otp_verification(sender_id, value, platform, ceo_id)
        
        elif intent == 'otp_only':
            # Direct OTP input (8 characters)
            return await self.handle_otp_verification(sender_id, value, platform, ceo_id)
        
        elif intent == 'order_status':
            return await self.handle_order_status(sender_id, value, platform, ceo_id)
        
        elif intent == 'upload':
            return await self.handle_upload_request(sender_id, platform, ceo_id)
        
        elif intent == 'help':
            return await self.handle_help(sender_id, platform)
        
        else:
            return await self.handle_unknown(sender_id, platform, text)
    
    async def handle_registration(
        self,
        sender_id: str,
        platform: str,
        ceo_id: str,
        parsed_message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle buyer registration flow.
        
        Flow:
        1. Check if buyer already exists
        2. If not, create buyer record
        3. Generate OTP
        4. Send welcome message + OTP
        
        Args:
            sender_id: Buyer ID (wa_* or ig_*)
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
            parsed_message: Full parsed message
        
        Returns:
            Dict with action result
        """
        try:
            # Check if buyer exists
            existing_buyer = get_buyer_by_id(sender_id)
            
            if existing_buyer:
                # Buyer already registered
                logger.info(f"Existing buyer: {sender_id}")
                
                # Generate new OTP
                otp = generate_otp('Buyer')
                store_otp(sender_id, otp, 'Buyer')
                
                # Send OTP
                if platform == 'whatsapp':
                    await self.whatsapp.send_otp(sender_id, otp)
                else:
                    await self.instagram.send_otp(sender_id, otp)
                
                return {
                    'action': 'otp_sent',
                    'buyer_id': sender_id,
                    'is_new': False,
                    'platform': platform
                }
            
            else:
                # New buyer - create account
                logger.info(f"Registering new buyer: {sender_id}")
                
                # Extract buyer details
                sender_phone = parsed_message.get('sender_phone')
                sender_name = parsed_message.get('sender_name', 'Customer')
                
                # Create buyer record
                buyer_data = {
                    'buyer_id': sender_id,
                    'platform': platform,
                    'phone_number': sender_phone,
                    'name': sender_name,
                    'ceo_id': ceo_id,
                    'registered_at': datetime.now(timezone.utc).isoformat(),
                    'status': 'pending_verification'
                }
                
                create_buyer(buyer_data)
                
                # Generate OTP
                otp = generate_otp('Buyer')
                store_otp(sender_id, otp, 'Buyer')
                
                # Send welcome message + OTP
                if platform == 'whatsapp':
                    await self.whatsapp.send_welcome_message(sender_id, sender_name)
                    await self.whatsapp.send_otp(sender_id, otp)
                else:
                    await self.instagram.send_welcome_message(sender_id, sender_name)
                    await self.instagram.send_otp(sender_id, otp)
                
                logger.info(
                    "Buyer registered successfully",
                    extra={
                        'buyer_id': sender_id,
                        'platform': platform,
                        'ceo_id': ceo_id
                    }
                )
                
                return {
                    'action': 'registered',
                    'buyer_id': sender_id,
                    'is_new': True,
                    'platform': platform,
                    'otp_sent': True
                }
        
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            
            # Send error message
            error_msg = "Sorry, we encountered an error. Please try again or contact support."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, error_msg)
            else:
                await self.instagram.send_message(sender_id, error_msg)
            
            return {
                'action': 'error',
                'error': str(e),
                'platform': platform
            }
    
    async def handle_otp_verification(
        self,
        sender_id: str,
        otp: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle OTP verification.
        
        Args:
            sender_id: Buyer ID
            otp: OTP code to verify
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with verification result
        """
        try:
            # Verify OTP
            is_valid = verify_otp(sender_id, otp, 'Buyer')
            
            if is_valid:
                logger.info(f"OTP verified for buyer: {sender_id}")
                
                # Send success message
                success_msg = """✅ Verification Successful!

Your account is now active! 🎉

You can now:
• Place orders
• Upload receipts
• Track deliveries

Type 'help' to see all commands"""
                
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, success_msg)
                else:
                    await self.instagram.send_message(sender_id, success_msg)
                
                return {
                    'action': 'verified',
                    'buyer_id': sender_id,
                    'platform': platform,
                    'valid': True
                }
            
            else:
                logger.warning(f"Invalid OTP attempt for buyer: {sender_id}")
                
                # Send error message
                error_msg = """❌ Invalid Verification Code

The code you entered is incorrect or expired.

• Codes expire after 5 minutes
• Each code can only be used once

Type 'register' to request a new code"""
                
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, error_msg)
                else:
                    await self.instagram.send_message(sender_id, error_msg)
                
                return {
                    'action': 'verification_failed',
                    'buyer_id': sender_id,
                    'platform': platform,
                    'valid': False
                }
        
        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}")
            
            error_msg = "Sorry, we encountered an error. Please try again."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, error_msg)
            else:
                await self.instagram.send_message(sender_id, error_msg)
            
            return {
                'action': 'error',
                'error': str(e),
                'platform': platform
            }
    
    async def handle_order_status(
        self,
        sender_id: str,
        order_id: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle order status check request.
        
        Args:
            sender_id: Buyer ID
            order_id: Order ID to check
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with order status
        """
        # TODO: Implement order status lookup from database
        logger.info(f"Order status request: {order_id} from {sender_id}")
        
        # Placeholder response
        msg = f"""📦 Order Status

Order ID: {order_id}

This feature is coming soon!

For now, please contact your vendor directly for order updates.

Type 'help' for other commands"""
        
        if platform == 'whatsapp':
            await self.whatsapp.send_message(sender_id, msg)
        else:
            await self.instagram.send_message(sender_id, msg)
        
        return {
            'action': 'order_status',
            'order_id': order_id,
            'platform': platform
        }
    
    async def handle_upload_request(
        self,
        sender_id: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle receipt upload request.
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with upload instructions
        """
        logger.info(f"Upload request from {sender_id}")
        
        # Placeholder response
        msg = """📸 Receipt Upload

To upload your payment receipt:

1. Make sure you have an active order
2. Your vendor will provide you with an upload link
3. Take a clear photo of your receipt
4. Click the link and upload

Need help? Just ask!

Type 'help' for other commands"""
        
        if platform == 'whatsapp':
            await self.whatsapp.send_message(sender_id, msg)
        else:
            await self.instagram.send_message(sender_id, msg)
        
        return {
            'action': 'upload_info',
            'platform': platform
        }
    
    async def handle_help(
        self,
        sender_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Send help message with available commands.
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
        
        Returns:
            Dict with action taken
        """
        msg = """🛡️ TrustGuard Help

Available Commands:

📝 *register* or *start*
   Create new account

🔐 *verify <code>*
   Verify your OTP code

📦 *order <order_id>*
   Check order status

📸 *upload*
   Receipt upload instructions

❓ *help*
   Show this message

---

Need more help?
Just message us anytime! We're here to assist. 💬

TrustGuard - Your Shopping Security Partner"""
        
        if platform == 'whatsapp':
            await self.whatsapp.send_message(sender_id, msg)
        else:
            await self.instagram.send_message(sender_id, msg)
        
        return {
            'action': 'help_sent',
            'platform': platform
        }
    
    async def handle_unknown(
        self,
        sender_id: str,
        platform: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Handle unknown/unrecognized messages.
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            text: Original message text
        
        Returns:
            Dict with action taken
        """
        logger.info(f"Unknown intent: '{text}' from {sender_id}")
        
        msg = """❓ I didn't understand that.

Try these commands:
• *register* - Create account
• *verify <code>* - Verify OTP
• *upload* - Upload receipt
• *help* - See all commands

Or just ask your question! 💬"""
        
        if platform == 'whatsapp':
            await self.whatsapp.send_message(sender_id, msg)
        else:
            await self.instagram.send_message(sender_id, msg)
        
        return {
            'action': 'unknown_intent',
            'platform': platform,
            'text': text
        }


# Singleton instance
chatbot_router = ChatbotRouter()


async def route_message(
    parsed_message: Dict[str, Any],
    ceo_id: str
) -> Dict[str, Any]:
    """
    Convenience function to route messages.
    
    Args:
        parsed_message: Parsed message dict
        ceo_id: CEO ID
    
    Returns:
        Dict with routing result
    """
    return await chatbot_router.route_message(parsed_message, ceo_id)
