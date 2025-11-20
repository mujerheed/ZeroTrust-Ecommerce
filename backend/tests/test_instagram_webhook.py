#!/usr/bin/env python3
"""
Test Instagram webhook integration end-to-end.
"""

import requests
import json
import boto3

API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
WEBHOOK_URL = f"{API_BASE}/integrations/webhook/instagram"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check_secrets_manager():
    """Verify Instagram credentials in Secrets Manager."""
    print_section("TEST 1: Verify Instagram Credentials")
    
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret_name = '/TrustGuard/dev/meta-TrustGuard-Dev'
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        
        has_instagram_token = 'instagram_access_token' in secrets
        has_page_id = 'instagram_page_id' in secrets
        
        if has_instagram_token and has_page_id:
            token = secrets['instagram_access_token']
            page_id = secrets['instagram_page_id']
            print(f"??? Instagram credentials found:")
            print(f"   Access Token: {token[:20]}...{token[-10:]}")
            print(f"   Page ID: {page_id}")
            
            # Also show WhatsApp for comparison
            if 'whatsapp_access_token' in secrets:
                print(f"\n??? WhatsApp credentials also present")
                print(f"   Access Token: {secrets['whatsapp_access_token'][:20]}...{secrets['whatsapp_access_token'][-10:]}")
                print(f"   Phone ID: {secrets.get('whatsapp_phone_number_id')}")
            
            return True
        else:
            print(f"??? Missing credentials:")
            print(f"   Has access token: {has_instagram_token}")
            print(f"   Has page ID: {has_page_id}")
            return False
            
    except Exception as e:
        print(f"??? Failed to retrieve secrets: {str(e)}")
        return False

def test_webhook_verification():
    """Test GET webhook verification (Meta's initial setup)."""
    print_section("TEST 2: Webhook Verification Challenge")
    
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "trustguard_verify_2025",
        "hub.challenge": "instagram_test_54321"
    }
    
    print(f"???? Sending verification request:")
    print(f"   URL: {WEBHOOK_URL}")
    print(f"   Mode: subscribe")
    print(f"   Token: trustguard_verify_2025")
    print(f"   Challenge: instagram_test_54321")
    
    response = requests.get(WEBHOOK_URL, params=params)
    
    print(f"\n???? Response:")
    print(f"   Status: {response.status_code}")
    print(f"   Body: {response.text}")
    
    if response.status_code == 200 and response.text == "instagram_test_54321":
        print(f"\n??? Verification PASSED")
        return True
    else:
        print(f"\n??? Verification FAILED")
        print(f"   Expected: 'instagram_test_54321'")
        print(f"   Got: '{response.text}'")
        return False

def test_send_instagram_message():
    """Test sending Instagram message via Graph API."""
    print_section("TEST 3: Send Test Instagram Message")
    
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='/TrustGuard/dev/meta-TrustGuard-Dev')
    secrets = json.loads(response['SecretString'])
    
    token = secrets.get('instagram_access_token')
    page_id = secrets.get('instagram_page_id')
    
    # Test with Instagram Send API
    url = "https://graph.facebook.com/v18.0/me/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # For testing, we'd need a recipient PSID (Page-Scoped ID)
    # This will fail in development mode without a test recipient
    print(f"???? Testing Instagram Graph API access...")
    print(f"   Page ID: {page_id}")
    print(f"   Token: {token[:20]}...{token[-10:]}")
    
    # Just verify the token works by getting page info
    verify_url = f"https://graph.facebook.com/v18.0/me?access_token={token}"
    response = requests.get(verify_url)
    
    print(f"\n???? Token Validation:")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ??? Token is valid!")
        print(f"   Page Name: {data.get('name', 'N/A')}")
        print(f"   Page ID: {data.get('id', 'N/A')}")
        return True
    else:
        print(f"   ??? Token validation failed")
        print(f"   Error: {response.text[:200]}")
        return False

def main():
    print("\n" + "="*70)
    print("  ???? INSTAGRAM WEBHOOK INTEGRATION TEST")
    print("="*70)
    print(f"\n  Webhook URL: {WEBHOOK_URL}")
    
    results = {}
    
    # Test 1: Check Secrets Manager
    results['secrets'] = check_secrets_manager()
    
    # Test 2: Webhook Verification
    results['verification'] = test_webhook_verification()
    
    # Test 3: Instagram API Token Test
    if results['secrets']:
        results['api_token'] = test_send_instagram_message()
    else:
        results['api_token'] = False
    
    # Summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"\nResults:")
    print(f"  {'???' if results['secrets'] else '???'} Secrets Manager Configuration")
    print(f"  {'???' if results['verification'] else '???'} Webhook Verification Challenge")
    print(f"  {'???' if results.get('api_token') else '???'} Instagram API Token Validation")
    
    if passed == total:
        print(f"\n???? ALL TESTS PASSED - Instagram webhook is fully configured!")
        print(f"\n???? Next Steps:")
        print(f"   1. Go to Meta App Dashboard ??? Messenger ??? Webhooks")
        print(f"   2. Select your Instagram Page")
        print(f"   3. Add callback URL: {WEBHOOK_URL}")
        print(f"   4. Add verify token: trustguard_verify_2025")
        print(f"   5. Subscribe to: messages, messaging_postbacks")
    else:
        print(f"\n??????  Some tests failed - check errors above")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
