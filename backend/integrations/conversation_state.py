"""
Conversation State Management for Multi-Turn Buyer Registration.

This module provides state persistence for conversational flows in WhatsApp/Instagram,
enabling multi-turn interactions for name/address/phone collection.

State Machine:
- initial → waiting_for_name → waiting_for_address → waiting_for_phone (IG only) → verified
- Supports interruptions (cancel, help)
- Auto-expires after 1 hour of inactivity (TTL)
"""

import time
from typing import Dict, Any, Optional
from common.db_connection import get_dynamodb_table
from common.config import settings
from common.logger import logger


class ConversationState:
    """
    Manages conversation state for multi-turn buyer registration flows.
    """
    
    def __init__(self):
        self.table = get_dynamodb_table(settings.CONVERSATION_STATE_TABLE)
        self.state_ttl = 3600  # 1 hour
    
    def save_state(
        self,
        buyer_id: str,
        state: str,
        context: Dict[str, Any],
        ceo_id: str,
        platform: str
    ) -> None:
        """
        Save or update conversation state for a buyer.
        
        Args:
            buyer_id: Buyer identifier (e.g., wa_1234567890, ig_9876543210)
            state: Current state (e.g., waiting_for_name, waiting_for_address)
            context: State-specific data (partial registration data, order context, etc.)
            ceo_id: CEO identifier for multi-tenancy
            platform: Platform (whatsapp or instagram)
        """
        timestamp = int(time.time())
        expires_at = timestamp + self.state_ttl
        
        item = {
            "buyer_id": buyer_id,
            "state": state,
            "context": context,
            "ceo_id": ceo_id,
            "platform": platform,
            "created_at": timestamp,
            "updated_at": timestamp,
            "expires_at": expires_at
        }
        
        self.table.put_item(Item=item)
        
        logger.info("Conversation state saved", extra={
            "buyer_id": buyer_id,
            "state": state,
            "platform": platform,
            "ceo_id": ceo_id
        })
    
    def get_state(self, buyer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve current conversation state for a buyer.
        
        Args:
            buyer_id: Buyer identifier
            
        Returns:
            State record or None if not found/expired
        """
        try:
            response = self.table.get_item(Key={"buyer_id": buyer_id})
            item = response.get("Item")
            
            if item:
                # Check if expired (DynamoDB TTL may not have cleaned up yet)
                if item.get("expires_at", 0) < int(time.time()):
                    logger.warning("Conversation state expired (TTL cleanup pending)", extra={
                        "buyer_id": buyer_id
                    })
                    self.delete_state(buyer_id)
                    return None
                
                logger.debug("Conversation state retrieved", extra={
                    "buyer_id": buyer_id,
                    "state": item.get("state")
                })
                return item
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get conversation state: {e}", extra={
                "buyer_id": buyer_id
            })
            return None
    
    def update_state(
        self,
        buyer_id: str,
        new_state: str,
        context_updates: Dict[str, Any]
    ) -> None:
        """
        Update conversation state and merge context.
        
        Args:
            buyer_id: Buyer identifier
            new_state: New state to transition to
            context_updates: Context fields to update/add
        """
        current = self.get_state(buyer_id)
        
        if current:
            # Merge context
            merged_context = {**current.get("context", {}), **context_updates}
            
            self.save_state(
                buyer_id=buyer_id,
                state=new_state,
                context=merged_context,
                ceo_id=current.get("ceo_id", settings.DEFAULT_CEO_ID),
                platform=current.get("platform", "whatsapp")
            )
        else:
            logger.warning("Attempted to update non-existent state", extra={
                "buyer_id": buyer_id,
                "new_state": new_state
            })
    
    def delete_state(self, buyer_id: str) -> None:
        """
        Delete conversation state (e.g., after registration complete or user cancels).
        
        Args:
            buyer_id: Buyer identifier
        """
        try:
            self.table.delete_item(Key={"buyer_id": buyer_id})
            logger.info("Conversation state deleted", extra={"buyer_id": buyer_id})
        except Exception as e:
            logger.error(f"Failed to delete conversation state: {e}", extra={
                "buyer_id": buyer_id
            })
    
    def get_context_value(self, buyer_id: str, key: str, default: Any = None) -> Any:
        """
        Get a specific value from conversation context.
        
        Args:
            buyer_id: Buyer identifier
            key: Context key to retrieve
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        state = self.get_state(buyer_id)
        if state:
            return state.get("context", {}).get(key, default)
        return default
    
    def is_in_conversation(self, buyer_id: str) -> bool:
        """
        Check if buyer is currently in an active conversation flow.
        
        Args:
            buyer_id: Buyer identifier
            
        Returns:
            True if active state exists, False otherwise
        """
        return self.get_state(buyer_id) is not None
    
    def reset_state(self, buyer_id: str, ceo_id: str, platform: str) -> None:
        """
        Reset conversation to initial state (e.g., after cancellation).
        
        Args:
            buyer_id: Buyer identifier
            ceo_id: CEO identifier
            platform: Platform (whatsapp or instagram)
        """
        self.save_state(
            buyer_id=buyer_id,
            state="initial",
            context={},
            ceo_id=ceo_id,
            platform=platform
        )


# State transition helpers

class ConversationFlow:
    """
    Defines valid state transitions and flow logic.
    """
    
    # State machine for buyer registration
    REGISTRATION_STATES = {
        "initial": "waiting_for_name",
        "waiting_for_name": "waiting_for_address",
        "waiting_for_address": "waiting_for_phone",  # Instagram only
        "waiting_for_phone": "waiting_for_otp",
        "waiting_for_otp": "verified"
    }
    
    # State machine for address confirmation (before order finalization)
    ADDRESS_CONFIRMATION_STATES = {
        "pending_address_confirmation": "confirmed",
        "confirmed": "order_finalized"
    }
    
    # States that can be interrupted
    INTERRUPTIBLE_STATES = [
        "waiting_for_name",
        "waiting_for_address",
        "waiting_for_phone",
        "waiting_for_otp",
        "pending_address_confirmation"
    ]
    
    # WhatsApp-specific flow (phone auto-detected)
    WHATSAPP_REGISTRATION_FLOW = [
        "initial",
        "waiting_for_name",
        "waiting_for_address",
        "waiting_for_otp",
        "verified"
    ]
    
    # Instagram-specific flow (need phone number)
    INSTAGRAM_REGISTRATION_FLOW = [
        "initial",
        "waiting_for_name",
        "waiting_for_address",
        "waiting_for_phone",
        "waiting_for_otp",
        "verified"
    ]
    
    @staticmethod
    def get_next_state(current_state: str, platform: str = "whatsapp") -> Optional[str]:
        """
        Get next state in registration flow.
        
        Args:
            current_state: Current state
            platform: Platform (whatsapp or instagram)
            
        Returns:
            Next state or None if at end of flow
        """
        if platform == "whatsapp":
            flow = ConversationFlow.WHATSAPP_REGISTRATION_FLOW
        else:
            flow = ConversationFlow.INSTAGRAM_REGISTRATION_FLOW
        
        try:
            current_index = flow.index(current_state)
            if current_index < len(flow) - 1:
                return flow[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    @staticmethod
    def is_final_state(state: str) -> bool:
        """
        Check if state is a terminal state.
        
        Args:
            state: State to check
            
        Returns:
            True if terminal state
        """
        return state in ["verified", "cancelled", "completed"]
    
    @staticmethod
    def can_interrupt(state: str) -> bool:
        """
        Check if current state can be interrupted (e.g., user types 'cancel').
        
        Args:
            state: State to check
            
        Returns:
            True if state can be interrupted
        """
        return state in ConversationFlow.INTERRUPTIBLE_STATES


# Singleton instance
conversation_state = ConversationState()
