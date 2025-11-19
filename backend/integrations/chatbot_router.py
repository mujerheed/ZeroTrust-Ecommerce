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
from ceo_service.ceo_logic import get_chatbot_settings


class ChatbotRouter:
    """Routes and processes chatbot messages."""
    
    # Intent patterns
    INTENT_PATTERNS = {
        'register': r'(?i)^(register|start|hi|hello|hey|begin)$',
        'verify_otp': r'(?i)^verify\s+([a-zA-Z0-9!@#$%^&*]{6,8})$',
        'otp_only': r'^([a-zA-Z0-9!@#$%^&*]{8})$',  # Direct 8-char OTP input
        'confirm_order': r'(?i)^(?:confirm|accept|yes|ok)(?:\s+(\S+))?$',  # confirm or confirm ord_123
        'cancel_order': r'(?i)^(?:cancel|reject|no)(?:\s+(\S+))?$',  # cancel or cancel ord_123
        'order_status': r'(?i)^(?:order|status)\s+(\S+)$',
        'upload': r'(?i)^(?:upload|receipt)$',
        'update_address': r'(?i)^(?:address|update address|my address)$',
        'help': r'(?i)^(?:help|\?)$'
    }
    
    def __init__(self):
        self.whatsapp = whatsapp_api
        self.instagram = instagram_api
    
    def get_customized_response(
        self,
        ceo_id: str,
        response_type: str,
        default_message: str,
        user_name: str = None
    ) -> str:
        """
        Get customized chatbot response based on CEO settings.
        
        Args:
            ceo_id: CEO ID for fetching settings
            response_type: Type of response ('welcome', 'greeting', 'thanks', 'goodbye', 'help')
            default_message: Fallback message if no customization
            user_name: Optional user name to personalize
        
        Returns:
            Customized message string
        """
        try:
            settings = get_chatbot_settings(ceo_id)
            
            # Get the appropriate custom response
            if response_type == 'welcome' and settings.get('welcome_message'):
                message = settings['welcome_message']
            elif response_type in ['greeting', 'thanks', 'goodbye', 'help']:
                auto_responses = settings.get('auto_responses', {})
                message = auto_responses.get(response_type, default_message)
            else:
                message = default_message
            
            # Personalize with user name if provided
            if user_name and '{name}' in message:
                message = message.replace('{name}', user_name)
            
            # Apply tone adjustments
            tone = settings.get('tone', 'friendly')
            message = self.apply_tone(message, tone)
            
            return message
            
        except Exception as e:
            logger.warning(f"Failed to get customized response: {str(e)}")
            return default_message
    
    def apply_tone(self, message: str, tone: str) -> str:
        """
        Apply tone adjustments to message.
        
        Args:
            message: Original message
            tone: Tone to apply ('friendly', 'professional', 'casual')
        
        Returns:
            Adjusted message
        """
        if tone == 'professional':
            # Remove excessive punctuation and emojis
            message = re.sub(r'!+', '.', message)
            message = re.sub(r'[😊👋🎉🛡️✨]', '', message)
        elif tone == 'casual':
            # Add friendly emoji if not present
            if not any(emoji in message for emoji in ['😊', '👋', '🎉', '✨']):
                message = message.rstrip() + ' 😊'
        
        return message
    
    def check_feature_enabled(self, ceo_id: str, feature_name: str) -> bool:
        """
        Check if a chatbot feature is enabled for this CEO.
        
        Args:
            ceo_id: CEO ID
            feature_name: Feature to check (e.g., 'address_collection', 'order_tracking')
        
        Returns:
            True if enabled, False otherwise
        """
        try:
            settings = get_chatbot_settings(ceo_id)
            enabled_features = settings.get('enabled_features', {})
            return enabled_features.get(feature_name, True)  # Default to enabled
        except Exception as e:
            logger.warning(f"Failed to check feature status: {str(e)}")
            return True  # Default to enabled on error
    
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
        
        elif intent == 'confirm_order':
            return await self.handle_order_confirmation(sender_id, value, platform, ceo_id)
        
        elif intent == 'cancel_order':
            return await self.handle_order_cancellation(sender_id, value, platform, ceo_id)
        
        elif intent == 'order_status':
            return await self.handle_order_status(sender_id, value, platform, ceo_id)
        
        elif intent == 'upload':
            return await self.handle_upload_request(sender_id, platform, ceo_id)
        
        elif intent == 'update_address':
            return await self.handle_address_update(sender_id, platform, ceo_id, text)
        
        elif intent == 'help':
            return await self.handle_help(sender_id, platform, ceo_id)
        
        else:
            return await self.handle_unknown(sender_id, platform, text, ceo_id)
    
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
                
                # Create buyer record with basic info
                # Note: Address will be collected later (during order placement or via follow-up)
                create_buyer(
                    buyer_id=sender_id,
                    phone=sender_phone,
                    platform=platform,
                    ceo_id=ceo_id,
                    name=sender_name,
                    delivery_address=None,  # Will be collected later
                    email=None,  # Optional, can be added later
                    meta=parsed_message.get('meta')
                )
                
                # Generate OTP
                otp = generate_otp('Buyer')
                store_otp(sender_id, otp, 'Buyer')
                
                # Get customized welcome message from CEO settings
                default_welcome = f"Hi {sender_name}! 👋\n\nThank you for choosing TrustGuard! 🛡️\n\nWe're here to make your online shopping safe and secure."
                welcome_message = self.get_customized_response(
                    ceo_id=ceo_id,
                    response_type='welcome',
                    default_message=default_welcome,
                    user_name=sender_name
                )
                
                # Send customized welcome message + OTP
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, welcome_message)
                    await self.whatsapp.send_otp(sender_id, otp)
                else:
                    await self.instagram.send_message(sender_id, welcome_message)
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
        # Check if order tracking is enabled
        if not self.check_feature_enabled(ceo_id, 'order_tracking'):
            msg = "Sorry, order tracking is currently unavailable. Please contact your vendor directly."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            return {'action': 'feature_disabled', 'feature': 'order_tracking', 'platform': platform}
        
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
        # Check if receipt upload is enabled
        if not self.check_feature_enabled(ceo_id, 'receipt_upload'):
            msg = "Sorry, receipt upload is currently unavailable. Please contact your vendor directly."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            return {'action': 'feature_disabled', 'feature': 'receipt_upload', 'platform': platform}
        
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
        platform: str,
        ceo_id: str = None
    ) -> Dict[str, Any]:
        """
        Send help message with available commands.
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID for customization (optional)
        
        Returns:
            Dict with action taken
        """
        # Check if help feature is enabled
        if ceo_id and not self.check_feature_enabled(ceo_id, 'help'):
            msg = "Sorry, help is currently unavailable. Please contact support directly."
        else:
            # Get customized help message or use default
            default_help = """🛡️ TrustGuard Help

Available Commands:

📝 *register* or *start*
   Create new account

🔐 *verify <code>*
   Verify your OTP code

📍 *address*
   Update delivery address

✅ *confirm*
   Confirm your pending order

❌ *cancel*
   Cancel your pending order

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
            
            if ceo_id:
                msg = self.get_customized_response(
                    ceo_id=ceo_id,
                    response_type='help',
                    default_message=default_help
                )
            else:
                msg = default_help
        
        if platform == 'whatsapp':
            await self.whatsapp.send_message(sender_id, msg)
        else:
            await self.instagram.send_message(sender_id, msg)
        
        return {
            'action': 'help_sent',
            'platform': platform
        }
    
    async def handle_order_confirmation(
        self,
        sender_id: str,
        order_id: Optional[str],
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle buyer confirming an order.
        
        Flow:
        1. If order_id provided, confirm that specific order
        2. If no order_id, fetch buyer's most recent pending order
        3. Update order status to 'confirmed'
        4. Send confirmation message
        
        Args:
            sender_id: Buyer ID
            order_id: Optional order ID (if buyer says "confirm ord_123")
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with action result
        """
        try:
            # Import here to avoid circular dependency
            from order_service.database import list_buyer_orders, update_order_status
            
            # If no order_id provided, get most recent pending order
            if not order_id:
                buyer_orders = list_buyer_orders(sender_id)
                pending_orders = [o for o in buyer_orders if o.get('status') == 'pending']
                
                if not pending_orders:
                    msg = "❌ You don't have any pending orders to confirm.\n\n"
                    msg += "Use *order <order_id>* to check your order status."
                    
                    if platform == 'whatsapp':
                        await self.whatsapp.send_message(sender_id, msg)
                    else:
                        await self.instagram.send_message(sender_id, msg)
                    
                    return {'action': 'no_pending_orders', 'platform': platform}
                
                # Get most recent (first in list, sorted by created_at desc)
                order_id = pending_orders[0].get('order_id')
            
            # Confirm the order
            updated_order = update_order_status(
                order_id=order_id,
                new_status='confirmed',
                notes='Confirmed by buyer via chatbot'
            )
            
            logger.info(f"Order {order_id} confirmed by buyer {sender_id}")
            
            # Send success message
            total = updated_order.get('total_amount', 0)
            currency_symbol = "₦" if updated_order.get('currency') == 'NGN' else updated_order.get('currency', '')
            
            msg = f"""✅ *Order Confirmed!*

📋 Order ID: `{order_id}`
💰 Total: {currency_symbol}{total:,.2f}

Your order has been confirmed successfully. 

📸 *Next Step:*
1. Make payment to the vendor
2. Reply with *'upload'* to submit your payment receipt

Thank you for shopping with us! 🛍️"""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            
            return {
                'action': 'order_confirmed',
                'order_id': order_id,
                'platform': platform
            }
            
        except Exception as e:
            logger.error(f"Order confirmation failed: {str(e)}")
            
            msg = f"❌ Failed to confirm order: {str(e)}\n\n"
            msg += "Please contact support if the issue persists."
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            
            return {'action': 'error', 'error': str(e), 'platform': platform}
    
    async def handle_order_cancellation(
        self,
        sender_id: str,
        order_id: Optional[str],
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle buyer cancelling an order.
        
        Flow:
        1. If order_id provided, cancel that specific order
        2. If no order_id, fetch buyer's most recent pending order
        3. Update order status to 'cancelled'
        4. Send cancellation confirmation
        
        Args:
            sender_id: Buyer ID
            order_id: Optional order ID (if buyer says "cancel ord_123")
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with action result
        """
        try:
            # Import here to avoid circular dependency
            from order_service.database import list_buyer_orders, update_order_status
            
            # If no order_id provided, get most recent pending order
            if not order_id:
                buyer_orders = list_buyer_orders(sender_id)
                cancellable_orders = [o for o in buyer_orders if o.get('status') in ['pending', 'confirmed']]
                
                if not cancellable_orders:
                    msg = "❌ You don't have any orders that can be cancelled.\n\n"
                    msg += "Only pending or confirmed orders can be cancelled."
                    
                    if platform == 'whatsapp':
                        await self.whatsapp.send_message(sender_id, msg)
                    else:
                        await self.instagram.send_message(sender_id, msg)
                    
                    return {'action': 'no_cancellable_orders', 'platform': platform}
                
                # Get most recent
                order_id = cancellable_orders[0].get('order_id')
            
            # Cancel the order
            updated_order = update_order_status(
                order_id=order_id,
                new_status='cancelled',
                notes='Cancelled by buyer via chatbot'
            )
            
            logger.info(f"Order {order_id} cancelled by buyer {sender_id}")
            
            # Send confirmation message
            msg = f"""❌ *Order Cancelled*

📋 Order ID: `{order_id}`

Your order has been cancelled successfully.

If you'd like to create a new order, please contact your vendor.

Thank you! 🙏"""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            
            return {
                'action': 'order_cancelled',
                'order_id': order_id,
                'platform': platform
            }
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {str(e)}")
            
            msg = f"❌ Failed to cancel order: {str(e)}\n\n"
            msg += "Please contact support if the issue persists."
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            
            return {'action': 'error', 'error': str(e), 'platform': platform}
    
    async def handle_address_update(
        self,
        sender_id: str,
        platform: str,
        ceo_id: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Handle delivery address update/collection.
        
        For new buyers or buyers updating address:
        1. Check if buyer has existing address
        2. If yes, show current address and ask for confirmation or new address
        3. If no, prompt for address
        4. Store address in buyer record
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
            text: Message text (may contain address if not just command)
        
        Returns:
            Dict with action result
        """
        from auth_service.database import update_user
        
        try:
            # Check if address collection is enabled
            if not self.check_feature_enabled(ceo_id, 'address_collection'):
                msg = "Sorry, address management is currently unavailable."
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, msg)
                else:
                    await self.instagram.send_message(sender_id, msg)
                return {'action': 'feature_disabled', 'feature': 'address_collection', 'platform': platform}
            
            # Get buyer record
            buyer = get_buyer_by_id(sender_id)
            if not buyer:
                msg = "⚠️ Please register first by typing 'register'"
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, msg)
                else:
                    await self.instagram.send_message(sender_id, msg)
                return {'action': 'not_registered', 'platform': platform}
            
            # Check if text contains address (more than just the command)
            # Simple heuristic: if message is longer than 20 chars, likely contains address
            address_text = text.strip()
            if len(address_text) > 20 and not address_text.lower() in ['address', 'update address', 'my address']:
                # User provided address in the message
                new_address = address_text
            else:
                # User just typed command, show current address or ask for it
                current_address = buyer.get('delivery_address')
                
                if current_address:
                    # Show current address and ask for confirmation
                    msg = f"""📍 Your current delivery address:

{current_address}

To update, reply with your new address.
Or type 'confirm' to keep this address."""
                else:
                    # No address on file, prompt for it
                    msg = """📍 Please provide your delivery address

Include:
• Street/building number
• Area/neighborhood
• City
• Landmark (optional)

Example: 15 Allen Avenue, Ikeja, Lagos. Near NNPC Station"""
                
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, msg)
                else:
                    await self.instagram.send_message(sender_id, msg)
                
                return {
                    'action': 'address_prompt',
                    'platform': platform,
                    'has_address': bool(current_address)
                }
            
            # Update buyer address
            update_user(sender_id, {'delivery_address': new_address})
            
            logger.info(
                "Buyer address updated",
                extra={
                    'buyer_id': sender_id,
                    'platform': platform,
                    'ceo_id': ceo_id
                }
            )
            
            msg = f"""✅ Delivery address updated!

📍 {new_address}

You can update this anytime by typing 'address' followed by your new address."""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            
            return {
                'action': 'address_updated',
                'platform': platform,
                'address': new_address
            }
        
        except Exception as e:
            logger.error(f"Address update failed: {str(e)}")
            
            msg = "Sorry, failed to update address. Please try again."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, msg)
            else:
                await self.instagram.send_message(sender_id, msg)
            
            return {'action': 'error', 'error': str(e), 'platform': platform}
    
    async def handle_unknown(
        self,
        sender_id: str,
        platform: str,
        text: str,
        ceo_id: str = None
    ) -> Dict[str, Any]:
        """
        Handle unknown/unrecognized messages.
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            text: Original message text
            ceo_id: CEO ID for customization (optional)
        
        Returns:
            Dict with action taken
        """
        logger.info(f"Unknown intent: '{text}' from {sender_id}")
        
        default_unknown_msg = """❓ I didn't understand that.

Try these commands:
• *register* - Create account
• *verify <code>* - Verify OTP
• *address* - Update delivery address
• *confirm* - Confirm order
• *cancel* - Cancel order
• *order <id>* - Check order status
• *upload* - Upload receipt
• *help* - See all commands

Or just ask your question! 💬"""
        
        # Get customized response if available
        if ceo_id:
            msg = self.get_customized_response(
                ceo_id=ceo_id,
                response_type='unknown',
                default_message=default_unknown_msg
            )
        else:
            msg = default_unknown_msg
        
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
