#!/usr/bin/env python3
"""
Final comprehensive CEO endpoint testing - fix remaining 3 failures
"""

import requests
import json
import boto3
from datetime import datetime
from hashlib import sha256

API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
ceo_email = "test.ceo@trustguard.com"

def get_ceo_token():
    """Get CEO authentication token"""
    # Login
    response = requests.post(f"{API_BASE}/auth/ceo/login", json={"contact": ceo_email})
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return None
    
    ceo_id = response.json().get("data", {}).get("ceo_id")
    print(f"✓ Login successful, CEO ID: {ceo_id}")
    
    # Inject test OTP
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    otps_table = dynamodb.Table('TrustGuard-OTPs-dev')
    
    test_otp = "Test@1"
    otp_hash = sha256(test_otp.encode()).hexdigest()
    
    otps_table.put_item(Item={
        'user_id': ceo_id,
        'request_id': 'req_9999999999_final',
        'otp_hash': otp_hash,
        'role': 'CEO',
        'expires_at': int(datetime.now().timestamp()) + 300,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    })
    
    # Verify OTP
    response = requests.post(
        f"{API_BASE}/auth/verify-otp",
        json={"user_id": ceo_id, "otp": test_otp}
    )
    
    if response.status_code == 200:
        token = response.json().get("data", {}).get("token")
        print(f"✓ OTP verified, token length: {len(token)}")
        return token, ceo_id
    else:
        print(f"❌ OTP verification failed: {response.status_code} - {response.text}")
        return None, None

def test_create_vendor(token):
    """Test POST /ceo/vendors"""
    print("\n" + "="*70)
    print("Testing: POST /ceo/vendors")
    print("="*70)
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Try different payloads
    test_cases = [
        {
            "name": "Test Case 1: All fields",
            "payload": {
                "name": "New Vendor",
                "email": f"vendor.{int(datetime.now().timestamp())}@test.com",
                "phone": "+2349012345678"
            }
        },
        {
            "name": "Test Case 2: Minimal fields",
            "payload": {
                "name": "Minimal Vendor",
                "email": f"minimal.{int(datetime.now().timestamp())}@test.com",
                "phone": "+2349087654321"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"  Payload: {json.dumps(test_case['payload'], indent=2)}")
        
        response = requests.post(
            f"{API_BASE}/ceo/vendors",
            headers=headers,
            json=test_case['payload']
        )
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 201:
            print(f"  ✓ SUCCESS!")
            print(f"  Response: {json.dumps(response.json(), indent=2)[:300]}")
            break
        else:
            print(f"  ✗ FAILED")
            print(f"  Error: {response.text[:200]}")

def test_request_approval_otp(token, ceo_id):
    """Test POST /ceo/approvals/request-otp"""
    print("\n" + "="*70)
    print("Testing: POST /ceo/approvals/request-otp")
    print("="*70)
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Try different payloads
    test_cases = [
        {"name": "With order_id", "payload": {"order_id": "test_order_123"}},
        {"name": "Empty payload", "payload": {}},
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"  Payload: {json.dumps(test_case['payload'])}")
        
        response = requests.post(
            f"{API_BASE}/ceo/approvals/request-otp",
            headers=headers,
            json=test_case['payload']
        )
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ SUCCESS!")
            print(f"  Response: {json.dumps(response.json(), indent=2)[:300]}")
            break
        else:
            print(f"  ✗ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")

def test_update_chatbot_settings(token):
    """Test PUT /ceo/chatbot/settings"""
    print("\n" + "="*70)
    print("Testing: PUT /ceo/chatbot/settings")
    print("="*70)
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Try different payloads
    test_cases = [
        {
            "name": "Full update",
            "payload": {
                "welcome_message": "Welcome! 🎉",
                "business_hours": "24/7",
                "tone": "friendly",
                "language": "en",
                "auto_responses": {
                    "greeting": "Hi there!",
                    "thanks": "You're welcome!"
                },
                "enabled_features": {
                    "order_tracking": True,
                    "receipt_upload": True
                }
            }
        },
        {
            "name": "Partial update",
            "payload": {
                "welcome_message": "Hello!",
                "tone": "professional"
            }
        },
        {
            "name": "Single field",
            "payload": {
                "welcome_message": "Updated message"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"  Payload: {json.dumps(test_case['payload'], indent=2)[:150]}")
        
        response = requests.put(
            f"{API_BASE}/ceo/chatbot/settings",
            headers=headers,
            json=test_case['payload']
        )
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ SUCCESS!")
            result = response.json()
            print(f"  Updated fields: {list(result.get('data', {}).keys())}")
            break
        else:
            print(f"  ✗ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")

def main():
    print("="*70)
    print("CEO ENDPOINT DEBUGGING - Fixing 3 Failed Endpoints")
    print("="*70)
    
    # Get token
    result = get_ceo_token()
    if not result or result[0] is None:
        print("\n❌ Failed to get CEO token. Exiting.")
        return
    
    token, ceo_id = result
    
    # Test failing endpoints
    test_create_vendor(token)
    test_request_approval_otp(token, ceo_id)
    test_update_chatbot_settings(token)
    
    print("\n" + "="*70)
    print("DEBUGGING COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
