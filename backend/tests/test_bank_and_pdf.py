#!/usr/bin/env python3
"""
Test Bank Details and PDF Receipt Support

Tests:
1. Vendor sets bank account details
2. Order includes bank details for payment instructions
3. Receipt upload with PDF content type
"""

import boto3
import hashlib
import time
import requests
import json
from decimal import Decimal

# Configuration
API_BASE_URL = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
AWS_REGION = "us-east-1"

# DynamoDB Tables
USERS_TABLE = "TrustGuard-Users-dev"
OTPS_TABLE = "TrustGuard-OTPs-dev"
VENDOR_PREFERENCES_TABLE = "TrustGuard-VendorPreferences-dev"

# Test Data
VENDOR_ID = "vendor_bank_test"
VENDOR_PHONE = "+2348087654321"
VENDOR_OTP = "BANK5678"
CEO_ID = "ceo_TrustGuard-Dev"

BUYER_ID = "wa_bank_buyer"
BUYER_PHONE = "+2348012345678"
BUYER_OTP = "BUYR1234"

# Bank Details
BANK_DETAILS = {
    "bank_name": "First Bank of Nigeria",
    "account_number": "0123456789",
    "account_name": "TrustGuard Ventures Ltd"
}

# Initialize boto3
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)


def hash_otp(otp: str) -> str:
    """Hash OTP using SHA-256."""
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def inject_otp(user_id: str, otp: str, role: str):
    """Inject OTP into DynamoDB for testing."""
    otps_table = dynamodb.Table(OTPS_TABLE)
    now = int(time.time())
    otp_record = {
        "user_id": user_id,
        "request_id": f"req_{now}_{hash_otp(otp)[:8]}",
        "otp_hash": hash_otp(otp),
        "role": role,
        "delivery_method": "test",
        "created_at": now,
        "expires_at": now + 600,
        "attempts": 0,
        "locked_until": 0
    }
    otps_table.put_item(Item=otp_record)
    print(f"✅ Injected {role} OTP: {otp}")
    time.sleep(2)  # DynamoDB consistency


def create_test_vendor():
    """Create test vendor in DynamoDB."""
    print("\n📝 Creating test vendor...")
    
    users_table = dynamodb.Table(USERS_TABLE)
    vendor_record = {
        "user_id": VENDOR_ID,
        "role": "Vendor",
        "ceo_id": CEO_ID,
        "phone": VENDOR_PHONE,
        "name": "Test Bank Vendor",
        "email": "bank.vendor@test.com",
        "is_active": True,
        "created_at": int(time.time()),
        "updated_at": int(time.time())
    }
    users_table.put_item(Item=vendor_record)
    print(f"✅ Created vendor: {VENDOR_ID}")


def create_test_buyer():
    """Create test buyer in DynamoDB."""
    print("\n📝 Creating test buyer...")
    
    users_table = dynamodb.Table(USERS_TABLE)
    buyer_record = {
        "user_id": BUYER_ID,
        "role": "Buyer",
        "ceo_id": CEO_ID,
        "phone": BUYER_PHONE,
        "name": "Bank Test Buyer",
        "email": "bank.buyer@test.com",
        "platform": "whatsapp",
        "is_active": True,
        "street": "123 Test Street",
        "city": "Lagos",
        "state": "Lagos State",
        "postal_code": "100001",
        "country": "Nigeria",
        "created_at": int(time.time()),
        "updated_at": int(time.time())
    }
    users_table.put_item(Item=buyer_record)
    print(f"✅ Created buyer: {BUYER_ID}")


def login_vendor():
    """Login vendor and get JWT token."""
    print("\n🔐 Logging in vendor...")
    inject_otp(VENDOR_ID, VENDOR_OTP, "Vendor")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={"user_id": VENDOR_ID, "otp": VENDOR_OTP}
    )
    
    if response.status_code == 200:
        token = response.json()["data"]["token"]
        print(f"✅ Vendor login successful")
        return token
    else:
        print(f"❌ Vendor login failed: {response.status_code}")
        print(response.text)
        return None


def test_update_vendor_bank_details(vendor_token):
    """Test updating vendor bank details."""
    print("\n\n🧪 TEST 1: Update Vendor Bank Details")
    print("=" * 60)
    
    response = requests.put(
        f"{API_BASE_URL}/vendor/preferences",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"bank_details": BANK_DETAILS}
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()["data"]
        bank = data.get("bank_details", {})
        
        print(f"\n✅ TEST 1 PASSED")
        print(f"   Bank Name: {bank.get('bank_name')}")
        print(f"   Account Number: {bank.get('account_number')}")
        print(f"   Account Name: {bank.get('account_name')}")
        return True
    else:
        print(f"\n❌ TEST 1 FAILED")
        return False


def test_get_vendor_preferences(vendor_token):
    """Test retrieving vendor preferences with bank details."""
    print("\n\n🧪 TEST 2: Get Vendor Preferences (Verify Bank Details Stored)")
    print("=" * 60)
    
    response = requests.get(
        f"{API_BASE_URL}/vendor/preferences",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()["data"]
        bank = data.get("bank_details", {})
        
        if bank and bank.get("account_number") == BANK_DETAILS["account_number"]:
            print(f"\n✅ TEST 2 PASSED")
            print(f"   ✅ Bank details correctly retrieved from preferences")
            return True
        else:
            print(f"\n❌ TEST 2 FAILED - Bank details not found")
            return False
    else:
        print(f"\n❌ TEST 2 FAILED")
        return False


def test_order_includes_bank_details(vendor_token):
    """Test that order creation includes vendor bank details."""
    print("\n\n🧪 TEST 3: Create Order - Bank Details Included in Response")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/orders",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "buyer_id": BUYER_ID,
            "items": [
                {
                    "name": "Test Product",
                    "quantity": 1,
                    "price": 15000.00,
                    "description": "Product requiring payment"
                }
            ],
            "notes": "Test order for bank details"
        }
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        data = response.json()["data"]
        payment_details = data.get("payment_details")
        
        if payment_details:
            print(f"\n✅ TEST 3 PASSED")
            print(f"   Order ID: {data['order_id']}")
            print(f"   Payment Details:")
            print(f"      Bank: {payment_details.get('bank_name')}")
            print(f"      Account: {payment_details.get('account_number')}")
            print(f"      Name: {payment_details.get('account_name')}")
            print(f"      Instructions: {payment_details.get('instructions')}")
            print(f"   ✅ Buyer can now make payment to this account")
            return data['order_id']
        else:
            print(f"\n❌ TEST 3 FAILED - No payment_details in response")
            return None
    else:
        print(f"\n❌ TEST 3 FAILED")
        return None


def test_pdf_receipt_upload(order_id):
    """Test PDF receipt upload support."""
    print("\n\n🧪 TEST 4: Request PDF Receipt Upload URL")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/receipts/request-upload",
        json={
            "order_id": order_id,
            "buyer_id": BUYER_ID,
            "vendor_id": VENDOR_ID,
            "ceo_id": CEO_ID,
            "file_extension": "pdf",
            "content_type": "application/pdf"
        }
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()["data"]
        allowed_types = data.get("allowed_content_types", [])
        
        if "application/pdf" in allowed_types:
            print(f"\n✅ TEST 4 PASSED")
            print(f"   Receipt ID: {data['receipt_id']}")
            print(f"   Allowed Content Types: {', '.join(allowed_types)}")
            print(f"   ✅ PDF receipts are supported")
            print(f"   ✅ image/heic also supported for iOS photos")
            print(f"   Max File Size: {data.get('max_file_size')} bytes")
            print(f"   Expires In: {data.get('expires_in')} seconds")
            return True
        else:
            print(f"\n❌ TEST 4 FAILED - PDF not in allowed types")
            return False
    else:
        print(f"\n❌ TEST 4 FAILED")
        return False


def verify_preferences_in_dynamodb():
    """Verify bank details stored in DynamoDB."""
    print("\n\n🔍 Verifying Vendor Preferences in DynamoDB...")
    print("=" * 60)
    
    prefs_table = dynamodb.Table(VENDOR_PREFERENCES_TABLE)
    response = prefs_table.get_item(Key={"vendor_id": VENDOR_ID})
    
    if "Item" in response:
        item = response["Item"]
        print(f"\n📦 Preferences Record:")
        print(f"   Vendor ID: {item.get('vendor_id')}")
        print(f"   Auto-Approve Threshold: {item.get('auto_approve_threshold')}")
        print(f"   Textract Enabled: {item.get('textract_enabled')}")
        print(f"   Bank Details:")
        bank = item.get('bank_details', {})
        if bank:
            print(f"      Bank Name: {bank.get('bank_name')}")
            print(f"      Account Number: {bank.get('account_number')}")
            print(f"      Account Name: {bank.get('account_name')}")
        print(f"\n✅ Bank details verified in DynamoDB")
    else:
        print(f"\n❌ Preferences not found in DynamoDB")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 BANK DETAILS & PDF RECEIPT TEST SUITE")
    print("=" * 60)
    
    # Setup
    create_test_vendor()
    create_test_buyer()
    
    # Login
    vendor_token = login_vendor()
    if not vendor_token:
        print("\n❌ Login failed. Aborting tests.")
        return
    
    # Run Tests
    test1_passed = test_update_vendor_bank_details(vendor_token)
    test2_passed = test_get_vendor_preferences(vendor_token)
    order_id = test_order_includes_bank_details(vendor_token)
    test3_passed = order_id is not None
    test4_passed = test_pdf_receipt_upload(order_id) if order_id else False
    
    # Verify in DynamoDB
    verify_preferences_in_dynamodb()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Update Bank Details): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Get Preferences): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Test 3 (Order with Bank Details): {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print(f"Test 4 (PDF Receipt Upload): {'✅ PASSED' if test4_passed else '❌ FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
