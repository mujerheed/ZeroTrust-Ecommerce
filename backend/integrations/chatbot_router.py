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
import time
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
    
    async def handle_message(self, parsed_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for handling incoming messages from webhooks.
        
        Extracts CEO ID from message metadata and routes to appropriate handler.
        
        Args:
            parsed_message: Parsed message dict from webhook_handler
        
        Returns:
            Dict with routing result
        """
        from integrations.webhook_handler import extract_ceo_id_from_metadata
        
        # Extract CEO ID for multi-tenancy routing
        ceo_id = extract_ceo_id_from_metadata(parsed_message)
        
        logger.info(
            "Processing message",
            extra={
                'platform': parsed_message.get('platform'),
                'sender': parsed_message.get('sender_id'),
                'ceo_id': ceo_id
            }
        )
        
        # Route to intent handler
        return await self.route_message(parsed_message, ceo_id)
    
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
        Route message to appropriate handler based on intent and conversation state.
        
        Args:
            parsed_message: Parsed message dict from webhook_handler
            ceo_id: CEO ID for multi-tenancy
        
        Returns:
            Dict with response and action taken
        """
        from integrations.conversation_state import conversation_state
        
        sender_id = parsed_message['sender_id']
        text = parsed_message.get('text', '').strip()
        platform = parsed_message['platform']
        media_id = parsed_message.get('media_id')
        media_type = parsed_message.get('media_type')
        media_url = parsed_message.get('media_url')  # Instagram provides direct URL
        
        logger.info(
            f"Routing message from {platform}",
            extra={
                'sender': sender_id,
                'text_preview': text[:50] if text else None,
                'has_media': bool(media_id or media_url),
                'media_type': media_type,
                'ceo_id': ceo_id
            }
        )
        
        # Handle media uploads (receipt images/videos) first
        if media_id or media_url:
            logger.info(f"Media detected: {media_type}", extra={'sender': sender_id})
            # Auto-download and process media
            download_result = await self.handle_media_download(
                sender_id, platform, media_id, media_url, media_type, ceo_id
            )
            # Continue processing text/caption if present
            if not text or text.startswith('['):
                # No caption or auto-generated text, just acknowledge upload
                return download_result
        
        # Check if buyer is in active conversation flow
        current_state = conversation_state.get_state(sender_id)
        
        if current_state:
            # Handle conversation flow continuation
            state_name = current_state.get('state')
            logger.info(f"Buyer {sender_id} in conversation state: {state_name}")
            
            # Check for interruptions (cancel, help)
            if text.lower() in ['cancel', 'stop', 'quit']:
                return await self.handle_cancel_conversation(sender_id, platform, ceo_id)
            elif text.lower() in ['help', '?']:
                return await self.handle_help(sender_id, platform, ceo_id)
            
            # Route based on current state
            if state_name == 'waiting_for_name':
                return await self.handle_name_collection(sender_id, text, platform, ceo_id)
            elif state_name == 'waiting_for_address':
                return await self.handle_address_collection(sender_id, text, platform, ceo_id)
            elif state_name == 'waiting_for_phone':
                return await self.handle_phone_collection(sender_id, text, platform, ceo_id)
            elif state_name == 'waiting_for_otp':
                return await self.handle_otp_verification(sender_id, text, platform, ceo_id)
            elif state_name == 'pending_address_confirmation':
                return await self.handle_address_confirmation_response(sender_id, text, platform, ceo_id)
        
        # No active conversation - detect intent from message
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
        Handle buyer registration flow with multi-turn conversation.
        
        Flow (WhatsApp):
        1. Greet buyer → Ask for name
        2. Store name → Ask for address
        3. Store address → Send OTP for phone verification
        
        Flow (Instagram):
        1. Greet buyer → Ask for name
        2. Store name → Ask for address
        3. Store address → Ask for phone
        4. Store phone → Send OTP for verification
        
        Args:
            sender_id: Buyer ID (wa_* or ig_*)
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
            parsed_message: Full parsed message
        
        Returns:
            Dict with action result
        """
        from integrations.conversation_state import conversation_state
        
        try:
            # Check if buyer exists
            existing_buyer = get_buyer_by_id(sender_id)
            
            if existing_buyer:
                # Buyer already registered - just send OTP
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
                # New buyer - start multi-turn registration
                logger.info(f"Starting multi-turn registration for: {sender_id}")
                
                # Get sender name from message (if available)
                sender_name = parsed_message.get('sender_name', 'there')
                
                # Get customized welcome message
                default_welcome = f"Hi {sender_name}! 👋\n\nWelcome to TrustGuard! 🛡️\n\nLet's get you set up."
                welcome_message = self.get_customized_response(
                    ceo_id=ceo_id,
                    response_type='welcome',
                    default_message=default_welcome,
                    user_name=sender_name
                )
                
                # Ask for name
                name_prompt = "\n\nWhat's your full name? 👤"
                
                # Send welcome + name prompt
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, welcome_message + name_prompt)
                else:
                    await self.instagram.send_message(sender_id, name_prompt)
                
                # Save conversation state
                conversation_state.save_state(
                    buyer_id=sender_id,
                    state='waiting_for_name',
                    context={
                        'platform_name': sender_name,  # Name from WhatsApp/Instagram profile
                        'started_at': int(time.time())
                    },
                    ceo_id=ceo_id,
                    platform=platform
                )
                
                logger.info(f"Conversation state saved: waiting_for_name for {sender_id}")
                
                return {
                    'action': 'registration_started',
                    'buyer_id': sender_id,
                    'is_new': True,
                    'platform': platform,
                    'state': 'waiting_for_name'
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
            sender_id: Buyer ID (may be PSID-based for Instagram)
            otp: OTP code to verify
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with verification result
        """
        from integrations.conversation_state import conversation_state
        
        try:
            # For Instagram, get phone-based buyer_id from conversation state
            buyer_id_for_verification = sender_id
            
            if platform == 'instagram' and sender_id.startswith('ig_'):
                # Check if this is PSID-based (not starting with 234)
                psid_part = sender_id.replace('ig_', '')
                if not psid_part.startswith('234'):
                    # This is PSID-based, get phone-based ID from conversation state
                    state = conversation_state.get_state(sender_id)
                    if state and 'phone_based_buyer_id' in state.get('context', {}):
                        buyer_id_for_verification = state['context']['phone_based_buyer_id']
                        logger.info(
                            f"Instagram OTP verification: Using phone-based ID {buyer_id_for_verification} "
                            f"for PSID {sender_id}"
                        )
            
            # Verify OTP with correct buyer_id
            is_valid = verify_otp(buyer_id_for_verification, otp, 'Buyer')
            
            if is_valid:
                logger.info(f"OTP verified for buyer: {buyer_id_for_verification}")
                
                # Send success message to original sender_id (for Instagram API)
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
                    'buyer_id': buyer_id_for_verification,  # Return phone-based ID
                    'original_sender_id': sender_id,         # Also return original
                    'platform': platform,
                    'valid': True
                }
            
            else:
                logger.warning(f"Invalid OTP attempt for buyer: {buyer_id_for_verification}")
                
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
                    'buyer_id': buyer_id_for_verification,
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
        
        # Look up order from database
        logger.info(f"Order status request: {order_id} from {sender_id}")
        
        try:
            from order_service.database import get_order_by_id
            order = get_order_by_id(order_id)
            
            if not order:
                msg = f"""❌ Order Not Found

Order ID: {order_id}

We couldn't find this order. Please check the order ID and try again.

Type 'help' for other commands"""
            elif order.get('buyer_id') != sender_id:
                # Security: Buyer can only view their own orders
                msg = """🔒 Access Denied

You can only view orders you placed.

Type 'help' for other commands"""
            else:
                # Format order status message
                status = order.get('status', 'unknown')
                amount = order.get('total_amount', 0)
                created = order.get('created_at', '')
                
                status_emoji = {
                    'pending': '⏳',
                    'confirmed': '✅',
                    'paid': '💰',
                    'verified': '🔐',
                    'shipped': '📦',
                    'delivered': '🎉',
                    'cancelled': '❌'
                }.get(status, '📋')
                
                msg = f"""{status_emoji} Order Status

Order ID: {order_id}
Status: {status.upper()}
Amount: ₦{amount:,.2f}

Need help? Type 'help' for commands"""
        
        except Exception as e:
            logger.error(f"Error fetching order: {str(e)}")
            msg = f"""⚠️ Error Checking Order

We had trouble looking up order {order_id}.

Please try again later or contact your vendor.

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
    
    # ========== Multi-Turn Conversation Handlers ==========
    
    async def handle_name_collection(
        self,
        sender_id: str,
        text: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle name collection step in registration flow.
        
        Args:
            sender_id: Buyer ID
            text: User's response (their name)
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with result
        """
        from integrations.conversation_state import conversation_state, ConversationFlow
        
        try:
            # Validate name (at least 2 characters)
            name = text.strip()
            if len(name) < 2:
                error_msg = "Please enter your full name (at least 2 characters)."
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, error_msg)
                else:
                    await self.instagram.send_message(sender_id, error_msg)
                return {'action': 'invalid_name', 'buyer_id': sender_id}
            
            # Update conversation state with name
            conversation_state.update_state(
                buyer_id=sender_id,
                new_state='waiting_for_address',
                context_updates={'name': name}
            )
            
            # Ask for address
            address_prompt = f"Thanks, {name}! 📍\n\nWhat's your delivery address?"
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, address_prompt)
            else:
                await self.instagram.send_message(sender_id, address_prompt)
            
            logger.info(f"Name collected for {sender_id}: {name}")
            
            return {
                'action': 'name_collected',
                'buyer_id': sender_id,
                'name': name,
                'next_state': 'waiting_for_address'
            }
        
        except Exception as e:
            logger.error(f"Name collection error: {str(e)}")
            return {'action': 'error', 'error': str(e)}
    
    async def handle_address_collection(
        self,
        sender_id: str,
        text: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle address collection step in registration flow.
        
        Args:
            sender_id: Buyer ID
            text: User's response (their address)
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with result
        """
        from integrations.conversation_state import conversation_state, ConversationFlow
        
        try:
            # Validate address (at least 10 characters)
            address = text.strip()
            if len(address) < 10:
                error_msg = "Please provide a complete delivery address (at least 10 characters).\n\nExample: 123 Ikeja Road, Lagos"
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, error_msg)
                else:
                    await self.instagram.send_message(sender_id, error_msg)
                return {'action': 'invalid_address', 'buyer_id': sender_id}
            
            # Get current state to retrieve name
            state = conversation_state.get_state(sender_id)
            name = state.get('context', {}).get('name', 'Customer')
            
            # Platform-specific flow
            if platform == 'whatsapp':
                # WhatsApp: Phone auto-detected, proceed to create buyer
                phone = state.get('context', {}).get('platform_phone', '')
                
                # Create buyer record
                create_buyer(
                    buyer_id=sender_id,
                    phone=phone,
                    platform=platform,
                    ceo_id=ceo_id,
                    name=name,
                    delivery_address=address,
                    email=None,
                    meta={}
                )
                
                # Generate OTP
                otp = generate_otp('Buyer')
                store_otp(sender_id, otp, 'Buyer')
                
                # Send OTP
                await self.whatsapp.send_otp(sender_id, otp)
                
                # Update state to waiting for OTP
                conversation_state.update_state(
                    buyer_id=sender_id,
                    new_state='waiting_for_otp',
                    context_updates={'address': address, 'phone': phone}
                )
                
                logger.info(f"Buyer created (WhatsApp): {sender_id}, OTP sent")
                
                return {
                    'action': 'otp_sent',
                    'buyer_id': sender_id,
                    'platform': platform,
                    'next_state': 'waiting_for_otp'
                }
            
            else:
                # Instagram: Need to ask for phone number
                conversation_state.update_state(
                    buyer_id=sender_id,
                    new_state='waiting_for_phone',
                    context_updates={'address': address}
                )
                
                phone_prompt = "Great! 📱\n\nWhat's your phone number? (Include country code, e.g., +2348012345678)"
                await self.instagram.send_message(sender_id, phone_prompt)
                
                logger.info(f"Address collected for {sender_id}, asking for phone")
                
                return {
                    'action': 'address_collected',
                    'buyer_id': sender_id,
                    'address': address,
                    'next_state': 'waiting_for_phone'
                }
        
        except Exception as e:
            logger.error(f"Address collection error: {str(e)}")
            return {'action': 'error', 'error': str(e)}
    
    async def handle_phone_collection(
        self,
        sender_id: str,
        text: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle phone number collection step (Instagram only).
        
        Args:
            sender_id: Buyer ID
            text: User's response (their phone number)
            platform: 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with result
        """
        from integrations.conversation_state import conversation_state
        from auth_service.utils import validate_phone_number
        
        try:
            # Validate phone number
            phone = text.strip()
            try:
                validate_phone_number(phone)
            except ValueError as e:
                error_msg = f"Invalid phone number: {str(e)}\n\nPlease provide a valid Nigerian phone number (+234...)."
                await self.instagram.send_message(sender_id, error_msg)
                return {'action': 'invalid_phone', 'buyer_id': sender_id}
            
            # Get current state to retrieve name and address
            state = conversation_state.get_state(sender_id)
            context = state.get('context', {})
            name = context.get('name', 'Customer')
            address = context.get('address', '')
            
            # Normalize phone to get consistent format
            from auth_service.auth_logic import normalize_phone
            normalized_phone = normalize_phone(phone)
            
            # Create phone-based buyer_id for Instagram (consistent with WhatsApp)
            # Format: ig_234XXXXXXXXXX (using phone instead of PSID)
            phone_digits = normalized_phone.replace('+', '')  # Remove + prefix
            phone_based_buyer_id = f"ig_{phone_digits}"
            
            # Extract original PSID from sender_id (format: ig_1234567890)
            original_psid = sender_id.replace('ig_', '') if sender_id.startswith('ig_') else sender_id
            
            # Create buyer record with phone-based ID
            create_buyer(
                buyer_id=phone_based_buyer_id,  # NEW: ig_234XXXXXXXXXX format
                phone=normalized_phone,
                platform=platform,
                ceo_id=ceo_id,
                name=name,
                delivery_address=address,
                email=None,
                meta={
                    'instagram_psid': original_psid,  # Store original PSID for reference
                    'original_sender_id': sender_id   # Store original sender_id
                }
            )
            
            # Generate OTP
            otp = generate_otp('Buyer')
            store_otp(phone_based_buyer_id, otp, 'Buyer')  # Use phone-based ID for OTP
            
            # Send OTP to original sender_id (PSID-based for Instagram API)
            await self.instagram.send_otp(sender_id, otp)
            
            # Update state with phone-based buyer_id
            conversation_state.update_state(
                buyer_id=sender_id,  # Keep using PSID for conversation state
                new_state='waiting_for_otp',
                context_updates={
                    'phone': normalized_phone,
                    'phone_based_buyer_id': phone_based_buyer_id  # Store for later reference
                }
            )
            
            logger.info(
                f"Buyer created (Instagram): Phone-based ID: {phone_based_buyer_id}, "
                f"Original PSID: {original_psid}, OTP sent"
            )
            
            return {
                'action': 'otp_sent',
                'buyer_id': phone_based_buyer_id,  # Return phone-based ID
                'original_sender_id': sender_id,    # Also return original for reference
                'platform': platform,
                'next_state': 'waiting_for_otp'
            }
        
        except Exception as e:
            logger.error(f"Phone collection error: {str(e)}")
            return {'action': 'error', 'error': str(e)}
    
    async def handle_cancel_conversation(
        self,
        sender_id: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle conversation cancellation (user types 'cancel').
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with result
        """
        from integrations.conversation_state import conversation_state
        
        try:
            # Delete conversation state
            conversation_state.delete_state(sender_id)
            
            cancel_msg = """❌ Registration Cancelled

No problem! You can start over anytime.

Type 'register' to begin again, or 'help' for assistance."""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, cancel_msg)
            else:
                await self.instagram.send_message(sender_id, cancel_msg)
            
            logger.info(f"Conversation cancelled for {sender_id}")
            
            return {
                'action': 'conversation_cancelled',
                'buyer_id': sender_id,
                'platform': platform
            }
        
        except Exception as e:
            logger.error(f"Cancel conversation error: {str(e)}")
            return {'action': 'error', 'error': str(e)}
    
    # ========== End Multi-Turn Handlers ==========
    
    async def handle_media_download(
        self,
        sender_id: str,
        platform: str,
        media_id: Optional[str],
        media_url: Optional[str],
        media_type: Optional[str],
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Auto-download and store receipt media (images/videos) to S3.
        
        Args:
            sender_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            media_id: WhatsApp media ID or Instagram media URL
            media_url: Direct media URL (Instagram) or None (WhatsApp)
            media_type: 'image', 'video', 'document', etc.
            ceo_id: CEO ID for S3 path
        
        Returns:
            Dict with upload result
        """
        from common.db_connection import get_s3_client
        from common.config import settings
        import uuid
        from datetime import datetime
        
        try:
            # Download media based on platform
            media_bytes = None
            
            if platform == 'whatsapp':
                # Step 1: Get media URL from media ID
                download_url = await self.whatsapp.get_media_url(media_id)
                if not download_url:
                    error_msg = "❌ Failed to retrieve media. Please try again."
                    await self.whatsapp.send_message(sender_id, error_msg)
                    return {'action': 'media_download_failed', 'reason': 'url_retrieval_failed'}
                
                # Step 2: Download media content
                media_bytes = await self.whatsapp.download_media(download_url)
            
            elif platform == 'instagram':
                # Instagram provides direct URL in webhook
                if media_url:
                    media_bytes = await self.instagram.download_media(media_url)
                else:
                    # Fallback: try to get URL from media_id
                    download_url = await self.instagram.get_media_url(media_id)
                    if download_url:
                        media_bytes = await self.instagram.download_media(download_url)
            
            if not media_bytes:
                error_msg = "❌ Failed to download media. Please try uploading again."
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, error_msg)
                else:
                    await self.instagram.send_message(sender_id, error_msg)
                return {'action': 'media_download_failed', 'reason': 'download_failed'}
            
            # Determine file extension from media type
            extension_map = {
                'image': 'jpg',
                'video': 'mp4',
                'document': 'pdf',
                'audio': 'mp3'
            }
            file_ext = extension_map.get(media_type, 'bin')
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.{file_ext}"
            
            # S3 path: receipts/{ceo_id}/pending-verification/{sender_id}/{filename}
            # (vendor_id unknown at upload time, moves to vendor folder after order creation)
            s3_key = f"receipts/{ceo_id}/pending-verification/{sender_id}/{filename}"
            
            # Upload to S3
            s3_client = get_s3_client()
            bucket_name = getattr(settings, 'RECEIPT_BUCKET', 'trustguard-receipts')
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=media_bytes,
                ContentType=f"{media_type}/*" if media_type else "application/octet-stream",
                ServerSideEncryption='AES256',
                Metadata={
                    'buyer_id': sender_id,
                    'ceo_id': ceo_id,
                    'platform': platform,
                    'media_type': media_type or 'unknown',
                    'upload_timestamp': timestamp
                }
            )
            
            logger.info(
                "Receipt media uploaded to S3",
                extra={
                    'buyer_id': sender_id,
                    'ceo_id': ceo_id,
                    'platform': platform,
                    'media_type': media_type,
                    's3_key': s3_key,
                    'file_size_kb': len(media_bytes) / 1024
                }
            )
            
            # Send acknowledgment to buyer
            success_msg = f"""✅ Receipt {media_type.capitalize()} Received!

Your payment proof has been securely uploaded.

📁 File: {filename}
📊 Status: Pending vendor verification

You'll be notified once your order is confirmed."""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, success_msg)
            else:
                await self.instagram.send_message(sender_id, success_msg)
            
            return {
                'action': 'media_uploaded',
                'buyer_id': sender_id,
                'media_type': media_type,
                's3_key': s3_key,
                'filename': filename,
                'file_size_bytes': len(media_bytes)
            }
        
        except Exception as e:
            logger.error(f"Media download error: {str(e)}", extra={'buyer_id': sender_id, 'platform': platform})
            
            error_msg = "❌ Upload failed due to technical error. Please try again or contact support."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, error_msg)
            else:
                await self.instagram.send_message(sender_id, error_msg)
            
            return {'action': 'media_download_error', 'error': str(e)}
    
    # ========== End Media Download ==========
    
    async def handle_address_confirmation_response(
        self,
        sender_id: str,
        text: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Handle buyer's response to address confirmation prompt.
        
        Buyer can:
        - Reply 'yes' to confirm current address
        - Reply 'update address to <new address>' to change address
        
        Args:
            sender_id: Buyer ID
            text: Buyer's response
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with action result
        """
        from integrations.conversation_state import conversation_state
        from auth_service.database import update_buyer
        from order_service.database import update_order_status, get_order
        import re
        
        try:
            # Get conversation state to retrieve order_id
            state = conversation_state.get_state(sender_id)
            if not state:
                error_msg = "❌ Session expired. Please try confirming your order again."
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, error_msg)
                else:
                    await self.instagram.send_message(sender_id, error_msg)
                return {'action': 'session_expired', 'buyer_id': sender_id}
            
            order_id = state.get('context', {}).get('order_id')
            current_address = state.get('context', {}).get('current_address', '')
            
            text_lower = text.lower().strip()
            
            # Check if buyer confirms current address
            if text_lower in ['yes', 'y', 'confirm', 'correct', 'ok', 'okay']:
                # Address confirmed - finalize order
                updated_order = update_order_status(
                    order_id=order_id,
                    new_status='confirmed',
                    notes='Confirmed by buyer via chatbot. Address verified.'
                )
                
                # Clear conversation state
                conversation_state.delete_state(sender_id)
                
                logger.info(f"Order {order_id} confirmed with address verification", extra={'buyer_id': sender_id})
                
                # Send success message
                total = updated_order.get('total_amount', 0)
                currency_symbol = "₦" if updated_order.get('currency') == 'NGN' else updated_order.get('currency', '')
                
                success_msg = f"""✅ *Order Confirmed!*

📋 Order ID: `{order_id}`
💰 Total: {currency_symbol}{total:,.2f}
📍 Delivery: _{current_address}_

Your order has been confirmed successfully. 

📸 *Next Step:*
1. Make payment to the vendor
2. Reply with *'upload'* to submit your payment receipt

Thank you for shopping with us! 🛍️"""
                
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, success_msg)
                else:
                    await self.instagram.send_message(sender_id, success_msg)
                
                return {
                    'action': 'order_confirmed',
                    'order_id': order_id,
                    'address_confirmed': True,
                    'platform': platform
                }
            
            # Check if buyer wants to update address
            update_pattern = r'update\s+address\s+to\s+(.+)'
            match = re.search(update_pattern, text_lower)
            
            if match or text_lower.startswith('update'):
                # Extract new address
                if match:
                    new_address = match.group(1).strip()
                else:
                    # Try to extract address after "update address to" or just "update"
                    parts = text.split(maxsplit=3)
                    new_address = parts[-1] if len(parts) > 2 else text
                
                # Validate address length
                if len(new_address) < 10:
                    error_msg = "❌ Please provide a complete delivery address (at least 10 characters).\n\nExample: _update address to 123 New Street, Lagos_"
                    if platform == 'whatsapp':
                        await self.whatsapp.send_message(sender_id, error_msg)
                    else:
                        await self.instagram.send_message(sender_id, error_msg)
                    return {'action': 'invalid_address', 'buyer_id': sender_id}
                
                # Update buyer's delivery address
                update_buyer(sender_id, {'delivery_address': new_address})
                
                # Update conversation state with new address
                conversation_state.update_state(
                    buyer_id=sender_id,
                    new_state='pending_address_confirmation',
                    context_updates={'current_address': new_address}
                )
                
                logger.info(f"Buyer {sender_id} updated address: {new_address}")
                
                # Ask for confirmation of new address
                reconfirm_msg = f"""📍 **Address Updated**

New delivery address:
_{new_address}_

Is this address correct?

Reply:
• *yes* to confirm and finalize order
• *update address to [another address]* to change again"""
                
                if platform == 'whatsapp':
                    await self.whatsapp.send_message(sender_id, reconfirm_msg)
                else:
                    await self.instagram.send_message(sender_id, reconfirm_msg)
                
                return {
                    'action': 'address_updated',
                    'buyer_id': sender_id,
                    'new_address': new_address,
                    'platform': platform
                }
            
            # Invalid response
            help_msg = """❓ I didn't understand that.

Please reply:
• *yes* to confirm current address
• *update address to [new address]* to change address

Example: _update address to 123 Main Street, Lagos_"""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, help_msg)
            else:
                await self.instagram.send_message(sender_id, help_msg)
            
            return {'action': 'invalid_response', 'buyer_id': sender_id}
        
        except Exception as e:
            logger.error(f"Address confirmation response error: {str(e)}", extra={'buyer_id': sender_id})
            
            error_msg = "❌ Failed to process response. Please try again or contact support."
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, error_msg)
            else:
                await self.instagram.send_message(sender_id, error_msg)
            
            return {'action': 'error', 'error': str(e)}
    
    # ========== End Address Confirmation ==========
    
    async def generate_and_send_order_pdf(
        self,
        order_id: str,
        buyer_id: str,
        platform: str,
        ceo_id: str
    ) -> Dict[str, Any]:
        """
        Generate PDF summary for completed order and send to buyer.
        
        Args:
            order_id: Order ID
            buyer_id: Buyer ID
            platform: 'whatsapp' or 'instagram'
            ceo_id: CEO ID
        
        Returns:
            Dict with result
        """
        from integrations.pdf_generator import pdf_generator
        from order_service.database import get_order
        from auth_service.database import get_buyer, get_user
        from common.db_connection import get_s3_client
        from common.config import settings
        import uuid
        from datetime import datetime, timedelta
        
        try:
            # Fetch order details
            order = get_order(order_id)
            if not order:
                logger.error(f"Order not found for PDF generation: {order_id}")
                return {'action': 'order_not_found', 'order_id': order_id}
            
            # Fetch buyer details
            buyer = get_buyer(buyer_id)
            if not buyer:
                logger.error(f"Buyer not found for PDF generation: {buyer_id}")
                return {'action': 'buyer_not_found', 'buyer_id': buyer_id}
            
            # Fetch vendor details (optional)
            vendor = None
            vendor_id = order.get('vendor_id')
            if vendor_id:
                vendor = get_user(vendor_id)
            
            # Get receipt URL if available
            receipt_url = None
            receipts = order.get('receipts', [])
            if receipts:
                # Get first verified receipt S3 key
                for receipt in receipts:
                    if receipt.get('verified'):
                        s3_key = receipt.get('s3_key')
                        if s3_key:
                            # Generate presigned URL (7 days validity)
                            s3_client = get_s3_client()
                            bucket_name = getattr(settings, 'RECEIPT_BUCKET', 'trustguard-receipts')
                            receipt_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': bucket_name, 'Key': s3_key},
                                ExpiresIn=604800  # 7 days
                            )
                            break
            
            # Generate PDF
            pdf_bytes = pdf_generator.generate_order_pdf(
                order=order,
                buyer=buyer,
                vendor=vendor,
                receipt_url=receipt_url
            )
            
            # Upload PDF to S3
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"order_{order_id}_{timestamp}.pdf"
            s3_key = f"invoices/{ceo_id}/{buyer_id}/{pdf_filename}"
            
            s3_client = get_s3_client()
            bucket_name = getattr(settings, 'RECEIPT_BUCKET', 'trustguard-receipts')
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType='application/pdf',
                ServerSideEncryption='AES256',
                Metadata={
                    'order_id': order_id,
                    'buyer_id': buyer_id,
                    'ceo_id': ceo_id,
                    'generated_at': timestamp
                }
            )
            
            # Generate presigned download URL (7 days validity)
            pdf_download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=604800  # 7 days
            )
            
            logger.info(
                "Order PDF generated and uploaded",
                extra={
                    'order_id': order_id,
                    'buyer_id': buyer_id,
                    's3_key': s3_key,
                    'pdf_size_kb': len(pdf_bytes) / 1024
                }
            )
            
            # Send PDF download link to buyer
            total = order.get('total_amount', 0)
            currency = order.get('currency', 'NGN')
            currency_symbol = "₦" if currency == 'NGN' else currency
            
            message = f"""🎉 *Order Complete!*

Thank you for your purchase!

📋 Order ID: `{order_id}`
💰 Total: {currency_symbol}{total:,.2f}
✅ Status: Completed

📄 **Transaction Summary PDF**
Your detailed invoice is ready for download:

{pdf_download_url}

_Link expires in 7 days_

Thank you for choosing TrustGuard! 🛍️"""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(buyer_id, message)
            else:
                await self.instagram.send_message(buyer_id, message)
            
            return {
                'action': 'pdf_generated_and_sent',
                'order_id': order_id,
                'buyer_id': buyer_id,
                's3_key': s3_key,
                'download_url': pdf_download_url,
                'pdf_size_bytes': len(pdf_bytes)
            }
        
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}", extra={'order_id': order_id, 'buyer_id': buyer_id})
            return {'action': 'pdf_generation_error', 'error': str(e)}
    
    # ========== End PDF Generation ==========
    
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
        3. **NEW: Ask for delivery address confirmation before finalizing**
        4. Update order status to 'confirmed'
        5. Send confirmation message
        
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
            from auth_service.database import get_buyer
            from integrations.conversation_state import conversation_state
            
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
            
            # **NEW: Address Confirmation Step**
            # Get buyer's delivery address
            buyer = get_buyer(sender_id)
            delivery_address = buyer.get('delivery_address', 'Not provided')
            
            # Save conversation state to wait for address confirmation
            conversation_state.save_state(
                buyer_id=sender_id,
                state='pending_address_confirmation',
                context={
                    'order_id': order_id,
                    'current_address': delivery_address
                },
                ceo_id=ceo_id,
                platform=platform
            )
            
            # Ask buyer to confirm address
            confirmation_msg = f"""📍 **Delivery Address Confirmation**

Current delivery address:
_{delivery_address}_

Is this address correct?

Reply:
• *yes* to confirm and proceed
• *update address to [new address]* to change address

Example: _update address to 123 New Street, Lagos_"""
            
            if platform == 'whatsapp':
                await self.whatsapp.send_message(sender_id, confirmation_msg)
            else:
                await self.instagram.send_message(sender_id, confirmation_msg)
            
            logger.info(f"Address confirmation requested for order {order_id}", extra={'buyer_id': sender_id})
            
            return {
                'action': 'address_confirmation_requested',
                'order_id': order_id,
                'platform': platform,
                'address': delivery_address
            }
            
        except Exception as e:
            logger.error(f"Order confirmation failed: {str(e)}")
            
            msg = f"❌ Failed to process order confirmation: {str(e)}\n\n"
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
