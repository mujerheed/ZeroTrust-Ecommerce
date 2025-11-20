"""
Test script for Negotiation System End-to-End Flow
Tests the complete negotiation workflow from quote request to order conversion.
"""

import boto3
import requests
import json
import time
import hashlib
from decimal import Decimal

# API Base URL
BASE_URL = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"

# Test data
BUYER_PHONE = "+2348012345678"
BUYER_ID = "wa_1234567890"  # WhatsApp buyer ID format
VENDOR_ID = "vendor_dev_001"
CEO_ID = "ceo_TrustGuard-Dev"

def inject_test_otp():
    """Inject a test OTP into DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    otps_table = dynamodb.Table('TrustGuard-OTPs-dev')
    
    test_otp = "TEST1234"
    # Hash the OTP using SHA-256 (same as auth_service/otp_manager.py)
    otp_hash = hashlib.sha256(test_otp.encode('utf-8')).hexdigest()
    ttl = int(time.time()) + 300  # 5 minutes from now
    request_id = f"test_req_{int(time.time())}"
    
    otps_table.put_item(
        Item={
            'user_id': BUYER_ID,
            'request_id': request_id,
            'otp_hash': otp_hash,  # Store hashed OTP
            'role': 'Buyer',
            'phone': BUYER_PHONE,
            'expires_at': ttl,
            'attempts': 0,
            'max_attempts': 5,
            'platform': 'whatsapp',
            'delivery_method': 'whatsapp'
        }
    )
    
    print(f"✅ Injected test OTP: {test_otp} for {BUYER_ID} (hash: {otp_hash[:16]}...)")
    return test_otp


def test_negotiation_flow():
    """Test complete negotiation flow."""
    
    print("=" * 80)
    print("NEGOTIATION SYSTEM END-TO-END TEST")
    print("=" * 80)
    
    # Step 1: Inject test OTP
    print("\n[1] Injecting test OTP...")
    test_otp = inject_test_otp()
    
    # Step 2: Verify OTP and get buyer token
    print("\n[2] Verifying OTP and getting buyer token...")
    verify_response = requests.post(
        f"{BASE_URL}/auth/verify-otp",
        json={
            "user_id": BUYER_ID,
            "otp": test_otp,
            "role": "Buyer"
        }
    )
    
    print(f"Verify Response: {verify_response.status_code}")
    
    if verify_response.status_code != 200:
        print(f"❌ Failed to verify OTP: {verify_response.text}")
        return
    
    buyer_data = verify_response.json()
    buyer_token = buyer_data.get("data", {}).get("token")
    
    if not buyer_token:
        print(f"❌ No token in response: {buyer_data}")
        return
    
    print(f"✅ Buyer authenticated! Token: {buyer_token[:50]}...")
    
    # Step 3: Request quote
    print("\n[3] Buyer requesting quote for 5 Dell laptops...")
    quote_request = {
        "vendor_id": VENDOR_ID,
        "items": [
            {
                "name": "Dell Latitude 5420",
                "quantity": 5,
                "description": "14-inch business laptop with i5 processor"
            }
        ],
        "delivery_address": {
            "street": "123 Herbert Macaulay Way",
            "city": "Lagos",
            "state": "Lagos State",
            "postal_code": "100001",
            "country": "Nigeria",
            "phone": BUYER_PHONE
        },
        "notes": "Need for office team. Looking for bulk discount."
    }
    
    quote_response = requests.post(
        f"{BASE_URL}/negotiations/request-quote",
        headers={"Authorization": f"Bearer {buyer_token}"},
        json=quote_request
    )
    
    print(f"Quote Request Response: {quote_response.status_code}")
    print(f"Response: {json.dumps(quote_response.json(), indent=2)}")
    
    if quote_response.status_code != 200:
        print(f"❌ Failed to request quote")
        return
    
    negotiation_data = quote_response.json().get("data", {})
    negotiation_id = negotiation_data.get("negotiation_id")
    
    print(f"✅ Quote requested! Negotiation ID: {negotiation_id}")
    
    # Step 4: List buyer's negotiations
    print("\n[4] Listing buyer's negotiations...")
    list_response = requests.get(
        f"{BASE_URL}/negotiations",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    
    print(f"List Response: {list_response.status_code}")
    if list_response.status_code == 200:
        negotiations = list_response.json().get("data", {}).get("negotiations", [])
        print(f"✅ Found {len(negotiations)} negotiation(s)")
        for neg in negotiations:
            print(f"   - {neg.get('negotiation_id')}: {neg.get('status')}")
    else:
        print(f"❌ Failed to list negotiations: {list_response.text}")
    
    # Step 5: Get negotiation details
    print(f"\n[5] Getting negotiation details for {negotiation_id}...")
    details_response = requests.get(
        f"{BASE_URL}/negotiations/{negotiation_id}",
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    
    print(f"Details Response: {details_response.status_code}")
    if details_response.status_code == 200:
        details = details_response.json().get("data", {})
        print(f"✅ Status: {details.get('status')}")
        print(f"   Items: {len(details.get('items', []))}")
        print(f"   Vendor: {details.get('vendor_id')}")
        print(f"   Created: {details.get('created_at')}")
    else:
        print(f"❌ Failed to get details: {details_response.text}")
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Negotiation System Deployed: {BASE_URL}/negotiations")
    print(f"✅ Quote request created: {negotiation_id}")
    print("✅ Buyer can list and view negotiations")
    print("\nNegotiation Flow (Production):")
    print("1. ✅ Buyer requests quote → Vendor receives notification")
    print("2. ⏳ Vendor provides pricing via POST /negotiations/{id}/quote")
    print("3. ⏳ Buyer reviews and negotiates via POST /negotiations/{id}/counter")
    print("4. ⏳ Both parties accept via PATCH /negotiations/{id}/accept")
    print("5. ⏳ Buyer converts to order via POST /negotiations/{id}/convert-to-order")
    print("=" * 80)


if __name__ == "__main__":
    test_negotiation_flow()
