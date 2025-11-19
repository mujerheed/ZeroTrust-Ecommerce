"""
Tests for Chatbot Customization Features

This test suite covers:
1. Get chatbot settings (defaults and custom)
2. Update chatbot settings (validation)
3. Preview chatbot conversation (intent detection)
4. Chatbot router integration (custom responses, tone, feature gates)

Run with: pytest backend/ceo_service/tests/test_chatbot_customization.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


# ==================== Test: Get Chatbot Settings ====================

def test_get_chatbot_settings_defaults():
    """Test getting default chatbot settings when none are set."""
    from ceo_service.ceo_logic import get_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'email': 'test@example.com'
        # No chatbot_settings field
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        settings = get_chatbot_settings('ceo_test_123')
        
        # Check defaults
        assert 'welcome_message' in settings
        assert 'business_hours' in settings
        assert settings['tone'] == 'friendly'
        assert settings['language'] == 'en'
        assert 'auto_responses' in settings
        assert 'greeting' in settings['auto_responses']
        assert 'enabled_features' in settings
        assert settings['enabled_features']['address_collection'] is True


def test_get_chatbot_settings_custom():
    """Test getting custom chatbot settings."""
    from ceo_service.ceo_logic import get_chatbot_settings
    
    custom_settings = {
        'welcome_message': 'Welcome to my store!',
        'tone': 'professional',
        'language': 'en',
        'auto_responses': {
            'greeting': 'Good day!'
        }
    }
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': custom_settings
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        settings = get_chatbot_settings('ceo_test_123')
        
        assert settings['welcome_message'] == 'Welcome to my store!'
        assert settings['tone'] == 'professional'


def test_get_chatbot_settings_ceo_not_found():
    """Test error when CEO doesn't exist."""
    from ceo_service.ceo_logic import get_chatbot_settings
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=None):
        with pytest.raises(ValueError, match="CEO.*not found"):
            get_chatbot_settings('nonexistent_ceo')


# ==================== Test: Update Chatbot Settings ====================

def test_update_chatbot_settings_welcome_message():
    """Test updating welcome message."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo), \
         patch('ceo_service.ceo_logic.update_ceo') as mock_update, \
         patch('ceo_service.ceo_logic.write_audit_log'):
        
        new_message = "👋 Welcome to Alice's Store! How may I help you?"
        updated = update_chatbot_settings(
            ceo_id='ceo_test_123',
            welcome_message=new_message
        )
        
        assert updated['welcome_message'] == new_message
        mock_update.assert_called_once()


def test_update_chatbot_settings_welcome_message_too_long():
    """Test validation: welcome message max 500 chars."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        long_message = "A" * 501
        
        with pytest.raises(ValueError, match="Welcome message too long"):
            update_chatbot_settings(
                ceo_id='ceo_test_123',
                welcome_message=long_message
            )


def test_update_chatbot_settings_tone():
    """Test updating tone."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo), \
         patch('ceo_service.ceo_logic.update_ceo') as mock_update, \
         patch('ceo_service.ceo_logic.write_audit_log'):
        
        updated = update_chatbot_settings(
            ceo_id='ceo_test_123',
            tone='professional'
        )
        
        assert updated['tone'] == 'professional'


def test_update_chatbot_settings_invalid_tone():
    """Test validation: tone must be friendly/professional/casual."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        with pytest.raises(ValueError, match="Invalid tone"):
            update_chatbot_settings(
                ceo_id='ceo_test_123',
                tone='robotic'
            )


def test_update_chatbot_settings_language():
    """Test updating language."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo), \
         patch('ceo_service.ceo_logic.update_ceo') as mock_update, \
         patch('ceo_service.ceo_logic.write_audit_log'):
        
        updated = update_chatbot_settings(
            ceo_id='ceo_test_123',
            language='fr'
        )
        
        assert updated['language'] == 'fr'


def test_update_chatbot_settings_invalid_language():
    """Test validation: language must be ISO 639-1."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        with pytest.raises(ValueError, match="Invalid language code"):
            update_chatbot_settings(
                ceo_id='ceo_test_123',
                language='english'
            )


def test_update_chatbot_settings_auto_responses():
    """Test updating auto-responses."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'greeting': 'Hello!',
                'thanks': 'Welcome!'
            }
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo), \
         patch('ceo_service.ceo_logic.update_ceo') as mock_update, \
         patch('ceo_service.ceo_logic.write_audit_log'):
        
        new_responses = {
            'greeting': 'Good day!',
            'goodbye': 'Farewell!'
        }
        
        updated = update_chatbot_settings(
            ceo_id='ceo_test_123',
            auto_responses=new_responses
        )
        
        # Should merge with existing
        assert updated['auto_responses']['greeting'] == 'Good day!'
        assert updated['auto_responses']['goodbye'] == 'Farewell!'
        assert updated['auto_responses']['thanks'] == 'Welcome!'  # Preserved


def test_update_chatbot_settings_enabled_features():
    """Test updating enabled features."""
    from ceo_service.ceo_logic import update_chatbot_settings
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'enabled_features': {
                'address_collection': True,
                'order_tracking': True
            }
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo), \
         patch('ceo_service.ceo_logic.update_ceo') as mock_update, \
         patch('ceo_service.ceo_logic.write_audit_log'):
        
        new_features = {
            'order_tracking': False,
            'receipt_upload': True
        }
        
        updated = update_chatbot_settings(
            ceo_id='ceo_test_123',
            enabled_features=new_features
        )
        
        # Should merge
        assert updated['enabled_features']['address_collection'] is True
        assert updated['enabled_features']['order_tracking'] is False
        assert updated['enabled_features']['receipt_upload'] is True


# ==================== Test: Preview Chatbot Conversation ====================

def test_preview_chatbot_greeting_intent():
    """Test preview with greeting intent."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'greeting': 'Hello! Welcome to our store.'
            },
            'tone': 'friendly'
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='Hello'
        )
        
        assert preview['user_message'] == 'Hello'
        assert preview['intent'] == 'greeting'
        assert 'Hello! Welcome to our store.' in preview['bot_response']


def test_preview_chatbot_thanks_intent():
    """Test preview with thanks intent."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'thanks': "You're very welcome!"
            },
            'tone': 'friendly'
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='Thank you so much!'
        )
        
        assert preview['intent'] == 'thanks'
        assert "You're very welcome!" in preview['bot_response']


def test_preview_chatbot_goodbye_intent():
    """Test preview with goodbye intent."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'goodbye': 'Have a wonderful day!'
            },
            'tone': 'friendly'
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='Goodbye'
        )
        
        assert preview['intent'] == 'goodbye'
        assert 'Have a wonderful day!' in preview['bot_response']


def test_preview_chatbot_help_intent():
    """Test preview with help intent."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='help'
        )
        
        assert preview['intent'] == 'help'
        assert 'help' in preview['bot_response'].lower()


def test_preview_chatbot_unknown_intent():
    """Test preview with unknown intent."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {}
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='asdfghjkl random text'
        )
        
        assert preview['intent'] == 'unknown'
        assert 'help' in preview['bot_response'].lower()


def test_preview_chatbot_professional_tone():
    """Test professional tone removes emojis and exclamation."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'greeting': 'Hello! Welcome! 😊'
            },
            'tone': 'professional'
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='Hi'
        )
        
        # Professional tone should remove ! and emojis
        assert '!' not in preview['bot_response'] or preview['bot_response'].count('!') == 0
        assert '😊' not in preview['bot_response']


def test_preview_chatbot_casual_tone():
    """Test casual tone adds friendly emoji."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'greeting': 'Hey there'
            },
            'tone': 'casual'
        }
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='Hello'
        )
        
        # Casual tone should add emoji
        assert '😊' in preview['bot_response']


def test_preview_chatbot_custom_settings_override():
    """Test preview with custom settings override."""
    from ceo_service.ceo_logic import preview_chatbot_conversation
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': {
            'auto_responses': {
                'greeting': 'Original greeting'
            },
            'tone': 'friendly'
        }
    }
    
    custom_settings = {
        'auto_responses': {
            'greeting': 'Custom preview greeting'
        },
        'tone': 'professional'
    }
    
    with patch('ceo_service.ceo_logic.get_ceo_by_id', return_value=mock_ceo):
        preview = preview_chatbot_conversation(
            ceo_id='ceo_test_123',
            user_message='Hi',
            settings=custom_settings
        )
        
        # Should use custom settings, not saved settings
        assert 'Custom preview greeting' in preview['bot_response']
        assert preview['settings_preview']['tone'] == 'professional'


# ==================== Test: Chatbot Router Integration ====================

def test_chatbot_router_customized_welcome():
    """Test chatbot router uses CEO's custom welcome message."""
    from integrations.chatbot_router import ChatbotRouter
    
    router = ChatbotRouter()
    
    # Mock CEO settings
    custom_settings = {
        'welcome_message': '🎉 Welcome to Bob\'s Boutique! {name}, we\'re glad you\'re here!',
        'tone': 'friendly'
    }
    
    mock_ceo = {
        'ceo_id': 'ceo_test_123',
        'chatbot_settings': custom_settings
    }
    
    with patch('integrations.chatbot_router.get_chatbot_settings', return_value=custom_settings):
        response = router.get_customized_response(
            ceo_id='ceo_test_123',
            response_type='welcome',
            default_message='Default welcome',
            user_name='Alice'
        )
        
        assert 'Bob\'s Boutique' in response
        assert 'Alice' in response


def test_chatbot_router_tone_application():
    """Test chatbot router applies tone correctly."""
    from integrations.chatbot_router import ChatbotRouter
    
    router = ChatbotRouter()
    
    # Test professional tone
    message = "Hello! Welcome! 😊"
    professional = router.apply_tone(message, 'professional')
    assert '!' not in professional or professional.count('!') < message.count('!')
    assert '😊' not in professional
    
    # Test casual tone
    message = "Hello"
    casual = router.apply_tone(message, 'casual')
    assert '😊' in casual


def test_chatbot_router_feature_enabled():
    """Test chatbot router checks feature gates."""
    from integrations.chatbot_router import ChatbotRouter
    
    router = ChatbotRouter()
    
    custom_settings = {
        'enabled_features': {
            'address_collection': True,
            'order_tracking': False
        }
    }
    
    with patch('integrations.chatbot_router.get_chatbot_settings', return_value=custom_settings):
        assert router.check_feature_enabled('ceo_test_123', 'address_collection') is True
        assert router.check_feature_enabled('ceo_test_123', 'order_tracking') is False


def test_chatbot_router_feature_disabled_defaults_enabled():
    """Test feature check defaults to enabled on error."""
    from integrations.chatbot_router import ChatbotRouter
    
    router = ChatbotRouter()
    
    with patch('integrations.chatbot_router.get_chatbot_settings', side_effect=Exception("DB error")):
        # Should default to enabled on error
        assert router.check_feature_enabled('ceo_test_123', 'address_collection') is True


# ==================== Manual Testing Guide ====================

"""
MANUAL TESTING GUIDE FOR CHATBOT CUSTOMIZATION
==============================================

Prerequisites:
1. Start FastAPI server: uvicorn backend.app:app --reload --port 8000
2. Have a valid CEO JWT token (register or login as CEO)
3. Use Postman, curl, or httpx

Test 1: Get Default Chatbot Settings
-------------------------------------
GET http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>

Expected:
- 200 OK
- Default settings returned (friendly tone, English, all features enabled)

Test 2: Update Welcome Message
-------------------------------
PATCH http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "welcome_message": "👋 Welcome to {name}'s favorite store! How can we help you today?"
}

Expected:
- 200 OK
- welcome_message updated in response

Test 3: Update Tone to Professional
-----------------------------------
PATCH http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "tone": "professional"
}

Expected:
- 200 OK
- tone updated to 'professional'

Test 4: Update Auto-Responses
------------------------------
PATCH http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "auto_responses": {
    "greeting": "Good day! How may I assist you?",
    "thanks": "You are most welcome.",
    "goodbye": "Have a pleasant day."
  }
}

Expected:
- 200 OK
- auto_responses updated

Test 5: Disable Feature (Order Tracking)
----------------------------------------
PATCH http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "enabled_features": {
    "order_tracking": false
  }
}

Expected:
- 200 OK
- order_tracking disabled

Test 6: Preview Chatbot (Greeting)
----------------------------------
POST http://localhost:8000/ceo/chatbot/preview
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "user_message": "Hello!"
}

Expected:
- 200 OK
- intent: "greeting"
- bot_response uses custom greeting if set

Test 7: Preview Chatbot (Unknown Intent)
----------------------------------------
POST http://localhost:8000/ceo/chatbot/preview
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "user_message": "random gibberish xyz123"
}

Expected:
- 200 OK
- intent: "unknown"
- bot_response suggests help

Test 8: Preview with Custom Settings (Not Saved)
-----------------------------------------------
POST http://localhost:8000/ceo/chatbot/preview
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "user_message": "Hi",
  "settings": {
    "tone": "casual",
    "auto_responses": {
      "greeting": "Hey there buddy"
    }
  }
}

Expected:
- 200 OK
- bot_response uses "Hey there buddy" with casual tone (emoji added)
- settings not saved (preview only)

Test 9: Validation Error - Invalid Tone
---------------------------------------
PATCH http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "tone": "robotic"
}

Expected:
- 400 Bad Request
- Error: "Tone must be one of: friendly, professional, casual"

Test 10: Validation Error - Welcome Too Long
--------------------------------------------
PATCH http://localhost:8000/ceo/chatbot-settings
Authorization: Bearer <CEO_JWT_TOKEN>
Content-Type: application/json

{
  "welcome_message": "<501 character string>"
}

Expected:
- 400 Bad Request
- Error: "Welcome message cannot exceed 500 characters"

Integration Test: Chatbot Router Uses CEO Settings
-------------------------------------------------
1. Update CEO chatbot settings (custom welcome, professional tone)
2. Send WhatsApp/Instagram message to trigger registration
3. Verify custom welcome message is sent
4. Verify tone is applied (no emojis, formal language)
5. Disable address_collection feature
6. Try to update address via chatbot
7. Verify error message: "address management is currently unavailable"

AWS Verification (After Deployment):
-----------------------------------
1. Check DynamoDB CEO record has chatbot_settings field
2. Verify settings persist across updates
3. Check audit logs for chatbot setting changes
4. Test Lambda function invocations for chatbot endpoints
"""
