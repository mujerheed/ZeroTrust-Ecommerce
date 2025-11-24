#!/usr/bin/env python3
"""
Test script to simulate WhatsApp/Instagram buyer interaction
Run this to test the bot without real Meta credentials
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_whatsapp_buyer_flow():
    """Simulate complete buyer flow via WhatsApp"""
    print("🤖 Testing WhatsApp Buyer Flow\n")
    
    buyer_phone = "2348012345678"
    buyer_id = f"wa_{buyer_phone}"
    
    # 1. Buyer sends initial message
    print("1️⃣  Buyer: Hello")
    webhook_payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": buyer_phone,
                        "type": "text",
                        "text": {"body": "Hello"},
                        "timestamp": str(int(time.time()))
                    }]
                }
            }]
        }]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/webhook/whatsapp",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Bot responded\n")
        else:
            print(f"   ❌ Error: {response.text}\n")
            return
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        print(f"   Make sure backend is running on {BASE_URL}\n")
        return
    
    # 2. Request OTP
    print("2️⃣  Requesting OTP for buyer")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/webhook/buyer-otp",
            json={
                "buyer_id": buyer_id,
                "otp": "test123",  # Mock OTP
                "platform": "whatsapp"
            }
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ OTP sent to buyer")
            print(f"   Dev OTP: {data.get('data', {}).get('dev_otp', 'N/A')}\n")
        else:
            print(f"   ❌ Error: {response.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # 3. Verify OTP
    print("3️⃣  Verifying OTP")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/verify-otp",
            json={
                "user_id": buyer_id,
                "otp": "test123"  # Use the OTP from step 2
            }
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get('data', {}).get('token')
            print(f"   ✅ OTP verified")
            print(f"   Token: {token[:50]}...\n")
            return token
        else:
            print(f"   ❌ Error: {response.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    return None


def test_instagram_buyer_flow():
    """Simulate buyer flow via Instagram"""
    print("📷 Testing Instagram Buyer Flow\n")
    
    buyer_ig = "1234567890"
    buyer_id = f"ig_{buyer_ig}"
    
    print("1️⃣  Buyer: Hello (Instagram DM)")
    webhook_payload = {
        "entry": [{
            "messaging": [{
                "sender": {"id": buyer_ig},
                "recipient": {"id": "your_page_id"},
                "timestamp": int(time.time() * 1000),
                "message": {
                    "mid": "m_test123",
                    "text": "Hello"
                }
            }]
        }]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/webhook/instagram",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Bot responded\n")
        else:
            print(f"   ❌ Error: {response.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")


def test_vendor_dashboard():
    """Test vendor can access dashboard"""
    print("🏪 Testing Vendor Dashboard Access\n")
    
    # This would use a vendor token from actual login
    print("   ℹ️  Login at: http://localhost:3001/vendor/login")
    print("   Use phone from DynamoDB vendors table\n")


def main():
    print("=" * 60)
    print("  TrustGuard Bot Testing Simulator")
    print("=" * 60)
    print()
    
    print("Choose test scenario:")
    print("1. WhatsApp Buyer Flow")
    print("2. Instagram Buyer Flow")
    print("3. Both")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    print()
    
    if choice == "1":
        test_whatsapp_buyer_flow()
    elif choice == "2":
        test_instagram_buyer_flow()
    elif choice == "3":
        test_whatsapp_buyer_flow()
        print("\n" + "=" * 60 + "\n")
        test_instagram_buyer_flow()
    else:
        print("Invalid choice")
        return
    
    print("\n" + "=" * 60)
    print("  Next Steps:")
    print("=" * 60)
    print("1. Check backend logs: tail -f /tmp/backend.log")
    print("2. Test vendor login: http://localhost:3001/vendor/login")
    print("3. Test CEO login: http://localhost:3001/ceo/login")
    print()


if __name__ == "__main__":
    main()
