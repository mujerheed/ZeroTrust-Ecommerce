# Integrations (integrations)

This module handles all external communication with WhatsApp Business API, Instagram Messaging API, SMS gateway, and incoming webhook handlers.

## Components

- `whatsapp_api.py`: Interaction with WhatsApp Business API.
- `instagram_api.py`: Integration with Instagram Messaging API.
- `sms_gateway.py`: SMS fallback service.
- `webhook_handler.py`: Endpoint to consume incoming messages/callbacks from external platforms.

## Setup

1. Add API credentials and secrets in module or project environment configuration.
2. Test webhook endpoints for connectivity.
3. Enable logging and error tracking.

## Usage

Supports OTP delivery, receipt uploads via messaging platforms, and syncs message events back to backend.

## Testing

Simulate webhook events with appropriate payloads to verify processing logic.
