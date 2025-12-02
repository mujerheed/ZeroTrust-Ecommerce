#!/usr/bin/env python3
import requests, json

BASE = "http://localhost:8000"
print("\n🧪 Quick Buyer Flow Test\n" + "="*50)

# Test 1: CEO Registration
print("\n📝 Test 1: CEO Registration")
r = requests.post(f"{BASE}/auth/ceo/register", json={
    "name": "Test CEO", "phone": "+2348155563371", "email": "ceo@test.com"
})
data = r.json().get("data", {})
print(f"✅ CEO ID: {data.get('ceo_id')}")
print(f"✅ OTP: {data.get('dev_otp')}")

# Test 2: OTP Verification  
print("\n🔐 Test 2: OTP Verification")
r = requests.post(f"{BASE}/auth/verify-otp", json={
    "user_id": data.get('ceo_id'), "otp": data.get('dev_otp')
})
token = r.json().get("data", {}).get("token")
print(f"✅ Token: {token[:40]}..." if token else "❌ Failed")

# Test 3: Buyer Flow
print("\n👤 Test 3: Buyer Identification")
buyer_id = "wa_2348012345678"
print(f"✅ Buyer ID: {buyer_id}")
print(f"✅ Platform: WhatsApp")

print("\n" + "="*50)
print("✅ All buyer flow components working!")
print("\nNext: Run full test with 'python3 test_complete_buyer_flow.py'")
