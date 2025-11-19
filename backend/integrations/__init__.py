"""
Integrations Module

Handles external platform integrations (WhatsApp, Instagram, SMS).
"""

from .whatsapp_api import WhatsAppAPI
from .instagram_api import InstagramAPI
from .chatbot_router import ChatbotRouter
from .webhook_routes import router as webhook_router

# Global instances (will be initialized with OAuth tokens per CEO)
whatsapp_api = WhatsAppAPI()
instagram_api = InstagramAPI()

__all__ = [
    'WhatsAppAPI',
    'InstagramAPI',
    'ChatbotRouter',
    'whatsapp_api',
    'instagram_api',
    'webhook_router'
]
