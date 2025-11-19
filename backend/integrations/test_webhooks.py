#!/usr/bin/env python3
"""
Test Meta Webhook Integration

Tests WhatsApp and Instagram webhook endpoints with mock payloads.
"""

import requests
import json
import hmac
import hashlib
from typing import Dict, Any


# Configuration
API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
APP_SECRET = "5ba4cd58e7205ecd439cf49ac11c7adb"  # From Secrets Manager
VERIFY_TOKEN = "trustguard_verify_2025"


def calculate_signature(payload: str) -> str:
    """Calculate X-Hub-Signature-256 for webhook payload."""
    signature = hmac.new(
        APP_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def test_whatsapp_verification():
    """Test WhatsApp webhook verification (GET)."""
    print("\n" + "="*60)
    print("TEST 1: WhatsApp Webhook Verification (GET)")
    print("="*60)
    
    url = f"{API_BASE}/integrations/webhook/whatsapp"
    params = {
        'hub.mode': 'subscribe',
        'hub.verify_token': VERIFY_TOKEN,
        'hub.challenge': '1234567890'
    }
    
    response = requests.get(url, params=params)
    
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200 and response.text == '1234567890':
        print("✅ PASS - Webhook verification successful")
        return True
    else:
        print("❌ FAIL - Webhook verification failed")
        return False


def test_instagram_verification():
    """Test Instagram webhook verification (GET)."""
    print("\n" + "="*60)
    print("TEST 2: Instagram Webhook Verification (GET)")
    print("="*60)
    
    url = f"{API_BASE}/integrations/webhook/instagram"
    params = {
        'hub.mode': 'subscribe',
        'hub.verify_token': VERIFY_TOKEN,
        'hub.challenge': '9876543210'
    }
    
    response = requests.get(url, params=params)
    
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200 and response.text == '9876543210':
        print("✅ PASS - Webhook verification successful")
        return True
    else:
        print("❌ FAIL - Webhook verification failed")
        return False


def test_whatsapp_message():
    """Test WhatsApp message webhook (POST)."""
    print("\n" + "="*60)
    print("TEST 3: WhatsApp Message Webhook (POST)")
    print("="*60)
    
    url = f"{API_BASE}/integrations/webhook/whatsapp"
    
    # Mock WhatsApp message payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": "123456789012345"
                    },
                    "contacts": [{
                        "profile": {"name": "Test User"},
                        "wa_id": "2348012345678"
                    }],
                    "messages": [{
                        "from": "2348012345678",
                        "id": "wamid.test123",
                        "timestamp": "1637074800",
                        "type": "text",
                        "text": {"body": "register"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    payload_str = json.dumps(payload)
    signature = calculate_signature(payload_str)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': signature
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)[:200]}...")
    print(f"Signature: {signature[:30]}...")
    
    response = requests.post(url, data=payload_str, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ PASS - Webhook accepted message")
        return True
    else:
        print("❌ FAIL - Webhook rejected message")
        return False


def test_instagram_message():
    """Test Instagram message webhook (POST)."""
    print("\n" + "="*60)
    print("TEST 4: Instagram Message Webhook (POST)")
    print("="*60)
    
    url = f"{API_BASE}/integrations/webhook/instagram"
    
    # Mock Instagram message payload
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "time": 1637074800,
            "messaging": [{
                "sender": {"id": "1234567890"},
                "recipient": {"id": "9876543210"},
                "timestamp": 1637074800,
                "message": {
                    "mid": "mid.test123",
                    "text": "hi"
                }
            }]
        }]
    }
    
    payload_str = json.dumps(payload)
    signature = calculate_signature(payload_str)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': signature
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)[:200]}...")
    print(f"Signature: {signature[:30]}...")
    
    response = requests.post(url, data=payload_str, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ PASS - Webhook accepted message")
        return True
    else:
        print("❌ FAIL - Webhook rejected message")
        return False


def test_invalid_signature():
    """Test webhook with invalid signature (should reject)."""
    print("\n" + "="*60)
    print("TEST 5: Invalid Signature Rejection")
    print("="*60)
    
    url = f"{API_BASE}/integrations/webhook/whatsapp"
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": []}]
    }
    
    payload_str = json.dumps(payload)
    
    # Use wrong signature
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': 'sha256=invalid_signature_here'
    }
    
    response = requests.post(url, data=payload_str, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 403:
        print("✅ PASS - Invalid signature rejected (403)")
        return True
    else:
        print("❌ FAIL - Should reject invalid signature with 403")
        return False


def main():
    """Run all webhook tests."""
    print("\n" + "="*60)
    print("Meta Webhook Integration Tests")
    print("="*60)
    print(f"API Base: {API_BASE}")
    print(f"App Secret: {APP_SECRET[:10]}...")
    print(f"Verify Token: {VERIFY_TOKEN}")
    
    results = []
    
    # Run tests
    results.append(("WhatsApp Verification", test_whatsapp_verification()))
    results.append(("Instagram Verification", test_instagram_verification()))
    results.append(("WhatsApp Message", test_whatsapp_message()))
    results.append(("Instagram Message", test_instagram_message()))
    results.append(("Invalid Signature", test_invalid_signature()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Meta integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check CloudWatch logs for details.")
        return 1


if __name__ == '__main__':
    exit(main())
