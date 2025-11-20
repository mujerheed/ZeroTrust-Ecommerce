#!/usr/bin/env python3
"""
Test WhatsApp webhook integration end-to-end.
"""

import requests
import json
import boto3
from datetime import datetime

API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
WEBHOOK_URL = f"{API_BASE}/integrations/webhook/whatsapp"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_webhook_verification():
    """Test GET webhook verification (Meta's initial setup)."""
    print_section("TEST 1: Webhook Verification Challenge")
    
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "trustguard_verify_2025",
        "hub.challenge": "test_challenge_12345"
    }
    
    response = requests.get(WEBHOOK_URL, params=params)
    
    if response.status_code == 200 and response.text == "test_challenge_12345":
        print(f"??? Verification PASSED")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return True
    else:
        print(f"??? Verification FAILED")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

def test_incoming_message():
    """Test POST webhook with incoming WhatsApp message."""
    print_section("TEST 2: Incoming WhatsApp Message")
    
    # Simulate Meta's webhook payload for incoming message
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "850791007281950",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+234813333xxxx",
                                "phone_number_id": "822785510918202"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": "2348099887766"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "2348099887766",
                                    "id": f"wamid.test_{int(datetime.now().timestamp())}",
                                    "timestamp": str(int(datetime.now().timestamp())),
                                    "text": {
                                        "body": "register"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    # Meta sends X-Hub-Signature-256 header for security
    # For testing, we'll skip HMAC validation or use a test signature
    headers = {
        "Content-Type": "application/json",
        # In production, Meta would send: "X-Hub-Signature-256": "sha256=..."
    }
    
    print("???? Sending test message payload:")
    print(f"   From: +2348099887766")
    print(f"   Message: 'register'")
    print(f"   Phone Number ID: 822785510918202")
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    
    print(f"\n???? Webhook Response:")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ??? Message received and processed")
        try:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=4)}")
        except:
            print(f"   Response: {response.text[:200]}")
        return True
    else:
        print(f"   ??? Message processing failed")
        print(f"   Error: {response.text[:500]}")
        return False

def check_buyer_created():
    """Check if buyer was created in DynamoDB."""
    print_section("TEST 3: Verify Buyer Registration in Database")
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    users_table = dynamodb.Table('TrustGuard-Users-dev')
    
    buyer_id = "wa_2348099887766"
    
    try:
        response = users_table.get_item(Key={'user_id': buyer_id})
        
        if 'Item' in response:
            buyer = response['Item']
            print(f"??? Buyer found in database:")
            print(f"   user_id: {buyer.get('user_id')}")
            print(f"   role: {buyer.get('role')}")
            print(f"   phone: {buyer.get('phone')}")
            print(f"   platform: {buyer.get('platform')}")
            print(f"   status: {buyer.get('status')}")
            print(f"   ceo_id: {buyer.get('ceo_id')}")
            return True
        else:
            print(f"??????  Buyer not found in database")
            print(f"   Expected user_id: {buyer_id}")
            return False
            
    except Exception as e:
        print(f"??? Database check failed: {str(e)}")
        return False

def check_secrets_manager():
    """Verify WhatsApp credentials in Secrets Manager."""
    print_section("TEST 0: Verify WhatsApp Credentials in Secrets Manager")
    
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret_name = '/TrustGuard/dev/meta-TrustGuard-Dev'
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        
        has_whatsapp_token = 'whatsapp_access_token' in secrets
        has_phone_id = 'whatsapp_phone_number_id' in secrets
        
        if has_whatsapp_token and has_phone_id:
            token = secrets['whatsapp_access_token']
            phone_id = secrets['whatsapp_phone_number_id']
            print(f"??? WhatsApp credentials found:")
            print(f"   Access Token: {token[:20]}...{token[-10:]}")
            print(f"   Phone Number ID: {phone_id}")
            return True
        else:
            print(f"??? Missing credentials:")
            print(f"   Has access token: {has_whatsapp_token}")
            print(f"   Has phone number ID: {has_phone_id}")
            return False
            
    except Exception as e:
        print(f"??? Failed to retrieve secrets: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("  ???? WHATSAPP WEBHOOK INTEGRATION TEST")
    print("="*70)
    print(f"\n  Webhook URL: {WEBHOOK_URL}")
    print(f"  Phone Number ID: 822785510918202")
    print(f"  Test Buyer: +2348099887766")
    
    results = {}
    
    # Test 0: Check Secrets Manager
    results['secrets'] = check_secrets_manager()
    
    # Test 1: Webhook Verification
    results['verification'] = test_webhook_verification()
    
    # Test 2: Incoming Message
    results['message'] = test_incoming_message()
    
    # Test 3: Database Check
    results['database'] = check_buyer_created()
    
    # Summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"\nResults:")
    print(f"  {'???' if results['secrets'] else '???'} Secrets Manager Configuration")
    print(f"  {'???' if results['verification'] else '???'} Webhook Verification Challenge")
    print(f"  {'???' if results['message'] else '???'} Incoming Message Processing")
    print(f"  {'???' if results['database'] else '???'} Buyer Database Registration")
    
    if passed == total:
        print(f"\n???? ALL TESTS PASSED - WhatsApp webhook is fully operational!")
    else:
        print(f"\n??????  Some tests failed - check errors above")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
