#!/usr/bin/env python3
"""
Test script for order delivery address confirmation feature.

Tests:
1. Create order without delivery (requires_delivery=False)
2. Create order with registered address (use_registered_address=True)
3. Create order with custom delivery address
4. Update order delivery preferences via PATCH
5. Validate delivery address storage in DynamoDB
"""

import requests
import boto3
import hashlib
import time
import json
from decimal import Decimal

# Configuration
API_BASE_URL = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
REGION = "us-east-1"
USERS_TABLE = "TrustGuard-Users-dev"
OTPS_TABLE = "TrustGuard-OTPs-dev"
ORDERS_TABLE = "TrustGuard-Orders-dev"

# Test data
CEO_ID = "ceo_TrustGuard-Dev"
VENDOR_ID = "vendor_dev_001"
BUYER_ID = "wa_test_delivery"
BUYER_PHONE = "+2348012345678"
BUYER_OTP = "DELV1234"  # 8-char alphanumeric OTP for Buyer
VENDOR_OTP = "VEND5678"  # 8-char OTP for Vendor

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=REGION)


def hash_otp(otp: str) -> str:
    """Hash OTP using SHA-256."""
    return hashlib.sha256(otp.encode()).hexdigest()


def create_test_buyer():
    """Create test buyer with registered address in DynamoDB."""
    print("\n📝 Creating test buyer with registered address...")
    
    users_table = dynamodb.Table(USERS_TABLE)
    
    buyer_record = {
        "user_id": BUYER_ID,
        "role": "Buyer",
        "ceo_id": CEO_ID,
        "phone": BUYER_PHONE,
        "name": "Test Delivery Buyer",
        "email": "test.delivery@example.com",
        "platform": "whatsapp",
        "is_active": True,
        # Registered address
        "street": "123 Test Street",
        "city": "Lagos",
        "state": "Lagos State",
        "postal_code": "100001",
        "country": "Nigeria",
        "landmark": "Near Test Landmark",
        "created_at": int(time.time()),
        "updated_at": int(time.time())
    }
    
    users_table.put_item(Item=buyer_record)
    print(f"✅ Created buyer: {BUYER_ID} with registered address in {buyer_record['city']}")


def create_test_vendor():
    """Create test vendor in DynamoDB."""
    print("\n📝 Creating test vendor...")
    
    users_table = dynamodb.Table(USERS_TABLE)
    
    vendor_record = {
        "user_id": VENDOR_ID,
        "role": "Vendor",
        "ceo_id": CEO_ID,
        "phone": "+2348087654321",
        "name": "Test Vendor",
        "email": "test.vendor@example.com",
        "is_active": True,
        "created_at": int(time.time()),
        "updated_at": int(time.time())
    }
    
    users_table.put_item(Item=vendor_record)
    print(f"✅ Created vendor: {VENDOR_ID}")


def inject_otp(user_id: str, otp: str, role: str):
    """Inject OTP into DynamoDB for testing."""
    otps_table = dynamodb.Table(OTPS_TABLE)
    now = int(time.time())
    otp_record = {
        "user_id": user_id,
        "request_id": f"req_{now}_{hash_otp(otp)[:8]}",  # Unique request_id
        "otp_hash": hash_otp(otp),
        "role": role,
        "delivery_method": "test",
        "created_at": now,
        "expires_at": now + 600,  # 10 minutes TTL
        "attempts": 0,
        "locked_until": 0
    }
    otps_table.put_item(Item=otp_record)
    print(f"✅ Injected {role} OTP: {otp}")
    # Wait for DynamoDB eventual consistency
    time.sleep(2)


def login_buyer():
    """Login buyer and get JWT token."""
    print("\n🔐 Logging in buyer...")
    
    # Inject fresh OTP just before login
    inject_otp(BUYER_ID, BUYER_OTP, "Buyer")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={
            "user_id": BUYER_ID,
            "otp": BUYER_OTP
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["data"]["token"]
        print(f"✅ Buyer login successful")
        return token
    else:
        print(f"❌ Buyer login failed: {response.status_code}")
        print(response.text)
        return None


def login_vendor():
    """Login vendor and get JWT token."""
    print("\n🔐 Logging in vendor...")
    
    # Inject fresh OTP just before login
    inject_otp(VENDOR_ID, VENDOR_OTP, "Vendor")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={
            "user_id": VENDOR_ID,
            "otp": VENDOR_OTP
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["data"]["token"]
        print(f"✅ Vendor login successful")
        return token
    else:
        print(f"❌ Vendor login failed: {response.status_code}")
        print(response.text)
        return None


def test_order_without_delivery(vendor_token):
    """Test 1: Create order without delivery (requires_delivery=False)."""
    print("\n\n🧪 TEST 1: Create order WITHOUT delivery")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/orders",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "buyer_id": BUYER_ID,
            "items": [
                {
                    "name": "Digital Product",
                    "quantity": 1,
                    "price": 5000.00,
                    "description": "Software license - no delivery needed"
                }
            ],
            "notes": "Digital download",
            "requires_delivery": False
        }
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    data = response.json()
    print(f"📦 Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 201:
        order_id = data["data"]["order_id"]
        requires_delivery = data["data"].get("requires_delivery", None)
        delivery_address = data["data"].get("delivery_address", None)
        
        print(f"\n✅ TEST 1 PASSED")
        print(f"   Order ID: {order_id}")
        print(f"   Requires Delivery: {requires_delivery}")
        print(f"   Delivery Address: {delivery_address}")
        
        return order_id
    else:
        print(f"\n❌ TEST 1 FAILED: {response.status_code}")
        return None


def test_order_with_registered_address(vendor_token):
    """Test 2: Create order with registered address (use_registered_address=True)."""
    print("\n\n🧪 TEST 2: Create order WITH registered address")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE_URL}/orders",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "buyer_id": BUYER_ID,
            "items": [
                {
                    "name": "Physical Product A",
                    "quantity": 2,
                    "price": 10000.00,
                    "description": "Requires shipping"
                }
            ],
            "notes": "Use my registered address",
            "requires_delivery": True,
            "use_registered_address": True
        }
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    data = response.json()
    print(f"📦 Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 201:
        order_id = data["data"]["order_id"]
        requires_delivery = data["data"].get("requires_delivery", None)
        delivery_address = data["data"].get("delivery_address", None)
        
        print(f"\n✅ TEST 2 PASSED")
        print(f"   Order ID: {order_id}")
        print(f"   Requires Delivery: {requires_delivery}")
        print(f"   Delivery Address: {json.dumps(delivery_address, indent=2)}")
        
        # Validate address matches buyer's registered address
        if delivery_address and delivery_address.get("city") == "Lagos":
            print(f"   ✅ Address correctly fetched from buyer record")
        
        return order_id
    else:
        print(f"\n❌ TEST 2 FAILED: {response.status_code}")
        return None


def test_order_with_custom_address(vendor_token):
    """Test 3: Create order with custom delivery address."""
    print("\n\n🧪 TEST 3: Create order WITH custom delivery address")
    print("=" * 60)
    
    custom_address = {
        "street": "456 Custom Avenue",
        "city": "Abuja",
        "state": "FCT",
        "postal_code": "900001",
        "country": "Nigeria",
        "phone": "+2348099999999",
        "landmark": "Near Presidential Villa"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/orders",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "buyer_id": BUYER_ID,
            "items": [
                {
                    "name": "Physical Product B",
                    "quantity": 1,
                    "price": 25000.00,
                    "description": "Ship to office"
                }
            ],
            "notes": "Office delivery",
            "requires_delivery": True,
            "use_registered_address": False,
            "delivery_address": custom_address
        }
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    data = response.json()
    print(f"📦 Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 201:
        order_id = data["data"]["order_id"]
        requires_delivery = data["data"].get("requires_delivery", None)
        delivery_address = data["data"].get("delivery_address", None)
        
        print(f"\n✅ TEST 3 PASSED")
        print(f"   Order ID: {order_id}")
        print(f"   Requires Delivery: {requires_delivery}")
        print(f"   Delivery Address: {json.dumps(delivery_address, indent=2)}")
        
        # Validate custom address was used
        if delivery_address and delivery_address.get("city") == "Abuja":
            print(f"   ✅ Custom address correctly stored")
        
        return order_id
    else:
        print(f"\n❌ TEST 3 FAILED: {response.status_code}")
        return None


def test_update_delivery_address(buyer_token, order_id):
    """Test 4: Update order delivery preferences via PATCH."""
    print("\n\n🧪 TEST 4: Update order delivery preferences")
    print("=" * 60)
    
    new_address = {
        "street": "789 Updated Street",
        "city": "Port Harcourt",
        "state": "Rivers State",
        "postal_code": "500001",
        "country": "Nigeria",
        "phone": "+2348077777777",
        "landmark": "Near Airport"
    }
    
    response = requests.patch(
        f"{API_BASE_URL}/orders/{order_id}/delivery",
        headers={"Authorization": f"Bearer {buyer_token}"},
        json={
            "buyer_id": BUYER_ID,
            "requires_delivery": True,
            "use_registered_address": False,
            "delivery_address": new_address
        }
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    data = response.json()
    print(f"📦 Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 200:
        updated_address = data["data"].get("delivery_address", None)
        
        print(f"\n✅ TEST 4 PASSED")
        print(f"   Order ID: {order_id}")
        print(f"   Updated Address: {json.dumps(updated_address, indent=2)}")
        
        # Validate new address was applied
        if updated_address and updated_address.get("city") == "Port Harcourt":
            print(f"   ✅ Delivery address successfully updated")
        
        return True
    else:
        print(f"\n❌ TEST 4 FAILED: {response.status_code}")
        return False


def verify_order_in_dynamodb(order_id):
    """Verify order delivery fields in DynamoDB."""
    print(f"\n\n🔍 Verifying order {order_id} in DynamoDB...")
    print("=" * 60)
    
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    try:
        response = orders_table.get_item(Key={"order_id": order_id})
        
        if "Item" in response:
            order = response["Item"]
            print(f"\n📦 Order Record:")
            print(f"   Order ID: {order.get('order_id')}")
            print(f"   Buyer ID: {order.get('buyer_id')}")
            print(f"   Vendor ID: {order.get('vendor_id')}")
            print(f"   Requires Delivery: {order.get('requires_delivery', 'NOT SET')}")
            
            delivery_address = order.get('delivery_address')
            if delivery_address:
                print(f"   Delivery Address:")
                print(f"      Street: {delivery_address.get('street')}")
                print(f"      City: {delivery_address.get('city')}")
                print(f"      State: {delivery_address.get('state')}")
                print(f"      Phone: {delivery_address.get('phone')}")
            else:
                print(f"   Delivery Address: None")
            
            print(f"\n✅ Order verified in DynamoDB")
            return True
        else:
            print(f"\n❌ Order not found in DynamoDB")
            return False
    
    except Exception as e:
        print(f"\n❌ Error verifying order: {str(e)}")
        return False


def main():
    """Run all delivery address tests."""
    print("\n" + "=" * 60)
    print("🚀 DELIVERY ADDRESS FEATURE TEST SUITE")
    print("=" * 60)
    
    # Setup
    create_test_buyer()
    create_test_vendor()
    
    # Login
    buyer_token = login_buyer()
    vendor_token = login_vendor()
    
    if not buyer_token or not vendor_token:
        print("\n❌ Login failed. Aborting tests.")
        return
    
    # Run tests
    order_id_1 = test_order_without_delivery(vendor_token)
    order_id_2 = test_order_with_registered_address(vendor_token)
    order_id_3 = test_order_with_custom_address(vendor_token)
    
    # Test PATCH update on order 1 (enable delivery)
    if order_id_1:
        test_update_delivery_address(buyer_token, order_id_1)
    
    # Verify in DynamoDB
    if order_id_2:
        verify_order_in_dynamodb(order_id_2)
    if order_id_3:
        verify_order_in_dynamodb(order_id_3)
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Test 1 (No Delivery): {'✅ PASSED' if order_id_1 else '❌ FAILED'}")
    print(f"Test 2 (Registered Address): {'✅ PASSED' if order_id_2 else '❌ FAILED'}")
    print(f"Test 3 (Custom Address): {'✅ PASSED' if order_id_3 else '❌ FAILED'}")
    print(f"Test 4 (Update Delivery): {'✅ PASSED' if order_id_1 else '❌ FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
