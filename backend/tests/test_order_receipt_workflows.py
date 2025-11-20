#!/usr/bin/env python3
"""
Comprehensive Order and Receipt Service Testing
Tests buyer workflows, order lifecycle, and receipt management
"""

import requests
import json
import boto3
from datetime import datetime
from hashlib import sha256
import time

# Consistent variable naming
API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
vendor_phone = "+2348133336318"
vendor_id = "ceo_test_001"  # Multi-role user
buyer_id = "wa_2348099887766"  # Test buyer (WhatsApp)
ceo_id = "ceo_test_001"

vendor_token = None
buyer_token = None

def print_section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")

def print_result(endpoint, status_code, success, data=None):
    status_icon = "✓" if success else "✗"
    print(f"[{status_icon}] {endpoint}: {status_code}")
    if data and success:
        print(f"    Data: {json.dumps(data, indent=4)[:200]}...")

def get_vendor_token():
    """Get vendor authentication token"""
    global vendor_token
    
    print_section("VENDOR AUTHENTICATION FOR ORDER CREATION")
    
    # Clean old OTPs for BOTH vendor and buyer
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    otps_table = dynamodb.Table('TrustGuard-OTPs-dev')
    
    # Clean vendor OTPs
    response_query = otps_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(vendor_id)
    )
    for item in response_query.get('Items', []):
        otps_table.delete_item(Key={
            'user_id': item['user_id'],
            'request_id': item['request_id']
        })
    
    # Clean buyer OTPs  
    response_query = otps_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(buyer_id)
    )
    for item in response_query.get('Items', []):
        otps_table.delete_item(Key={
            'user_id': item['user_id'],
            'request_id': item['request_id']
        })
    
    print("    OTP cleanup complete")
    time.sleep(2)  # Wait for cleanup to propagate
    
    # Request OTP
    response = requests.post(f"{API_BASE}/auth/vendor/login", json={"phone": vendor_phone})
    print_result("POST /auth/vendor/login", response.status_code, response.status_code == 200)
    
    if response.status_code != 200:
        print(f"    Error: {response.text[:200]}")
        return False
    
    # Inject test OTP
    test_otp = "Test@123"
    otp_hash = sha256(test_otp.encode()).hexdigest()
    
    otps_table.put_item(Item={
        'user_id': vendor_id,
        'request_id': f'req_{int(time.time())}_vendor_order',
        'otp_hash': otp_hash,
        'role': 'Vendor',
        'expires_at': int(datetime.now().timestamp()) + 300,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    })
    
    time.sleep(0.5)
    
    # Verify OTP
    response = requests.post(
        f"{API_BASE}/auth/verify-otp",
        json={"user_id": vendor_id, "otp": test_otp}
    )
    
    if response.status_code == 200:
        vendor_token = response.json().get('data', {}).get('token')
        print_result("POST /auth/verify-otp", response.status_code, True, 
                    {"token_length": len(vendor_token)})
        
        # Debug: decode token to check ceo_id
        import jwt
        decoded = jwt.decode(vendor_token, options={'verify_signature': False})
        print(f"    Token claims: sub={decoded.get('sub')}, role={decoded.get('role')}, ceo_id={decoded.get('ceo_id')}")
        
        return True
    else:
        print_result("POST /auth/verify-otp", response.status_code, False)
        return False

def setup_test_buyer():
    """Create test buyer in database"""
    print_section("SETUP TEST BUYER")
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    users_table = dynamodb.Table('TrustGuard-Users-dev')
    
    # Create buyer if doesn't exist
    try:
        users_table.put_item(Item={
            'user_id': buyer_id,
            'role': 'Buyer',
            'ceo_id': ceo_id,
            'platform': 'whatsapp',
            'phone': '+2348099887766',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'metadata': {
                'test_account': True
            }
        })
        print(f"    ✓ Created test buyer: {buyer_id}")
    except Exception as e:
        print(f"    ! Buyer may already exist: {str(e)[:100]}")

def get_buyer_token_via_webhook():
    """Simulate buyer OTP verification via webhook"""
    global buyer_token
    
    print_section("BUYER AUTHENTICATION VIA WEBHOOK")
    
    # Clean buyer OTPs
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    otps_table = dynamodb.Table('TrustGuard-OTPs-dev')
    
    response_query = otps_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(buyer_id)
    )
    for item in response_query.get('Items', []):
        otps_table.delete_item(Key={
            'user_id': item['user_id'],
            'request_id': item['request_id']
        })
    
    # Inject buyer OTP
    test_otp = "Buy@1234"  # 8-char buyer OTP
    otp_hash = sha256(test_otp.encode()).hexdigest()
    
    otps_table.put_item(Item={
        'user_id': buyer_id,
        'request_id': f'req_{int(time.time())}_buyer_test',
        'otp_hash': otp_hash,
        'role': 'Buyer',
        'expires_at': int(datetime.now().timestamp()) + 300,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    })
    
    time.sleep(0.5)
    
    # Call webhook endpoint - returns verified status, not token
    # For order/receipt testing, we'll use verify-otp endpoint instead
    response = requests.post(
        f"{API_BASE}/auth/verify-otp",
        json={
            "user_id": buyer_id,
            "otp": test_otp
        }
    )
    
    print_result("POST /auth/verify-otp (Buyer)", response.status_code, 
                response.status_code == 200)
    
    if response.status_code == 200:
        result = response.json()
        buyer_token = result.get('data', {}).get('token')
        if buyer_token:
            print(f"    Buyer token: {buyer_token[:50]}...")
            return True
        else:
            print(f"    Response: {json.dumps(result, indent=2)}")
    
    return False

def test_create_order():
    """Test creating an order"""
    print_section("CREATE ORDER")
    
    headers = {
        "Authorization": f"Bearer {vendor_token}",
        "Content-Type": "application/json"
    }
    
    order_data = {
        "buyer_id": buyer_id,
        "items": [
            {
                "name": "Test Product A",
                "quantity": 2,
                "price": 25000.00,
                "description": "Test product for order workflow"
            },
            {
                "name": "Test Product B",
                "quantity": 1,
                "price": 15000.00
            }
        ],
        "notes": "Test order for comprehensive testing"
    }
    
    response = requests.post(
        f"{API_BASE}/orders",
        headers=headers,
        json=order_data
    )
    
    print_result("POST /orders", response.status_code, 
                response.status_code == 201, 
                response.json() if response.status_code == 201 else None)
    
    if response.status_code == 201:
        order_id = response.json().get('data', {}).get('order_id')
        print(f"    Created order_id: {order_id}")
        return order_id
    else:
        print(f"    Error: {response.text[:200]}")
        return None

def test_get_order(order_id):
    """Test getting order details"""
    print_section("GET ORDER DETAILS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    response = requests.get(
        f"{API_BASE}/orders/{order_id}",
        headers=headers
    )
    
    print_result(f"GET /orders/{order_id}", response.status_code, 
                response.status_code == 200,
                response.json() if response.status_code == 200 else None)

def test_list_orders():
    """Test listing orders"""
    print_section("LIST ORDERS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # List all orders
    response = requests.get(f"{API_BASE}/orders", headers=headers)
    print_result("GET /orders", response.status_code, 
                response.status_code == 200,
                response.json() if response.status_code == 200 else None)
    
    # List with status filter
    response = requests.get(
        f"{API_BASE}/orders",
        headers=headers,
        params={"status": "pending"}
    )
    print_result("GET /orders?status=pending", response.status_code, 
                response.status_code == 200)

def test_confirm_order(order_id):
    """Test buyer confirming an order"""
    print_section("CONFIRM ORDER (BUYER)")
    
    headers = {"Authorization": f"Bearer {buyer_token}"}
    
    response = requests.patch(
        f"{API_BASE}/orders/{order_id}/confirm",
        headers=headers,
        json={"buyer_id": buyer_id}
    )
    
    print_result(f"PATCH /orders/{order_id}/confirm", response.status_code, 
                response.status_code == 200,
                response.json() if response.status_code == 200 else None)

def test_receipt_upload_flow(order_id):
    """Test receipt upload workflow"""
    print_section("RECEIPT UPLOAD WORKFLOW")
    
    # Step 1: Request upload URL
    headers = {"Authorization": f"Bearer {buyer_token}"}
    
    response = requests.post(
        f"{API_BASE}/receipts/request-upload",
        headers=headers,
        json={
            "order_id": order_id,
            "buyer_id": buyer_id,
            "file_type": "image/jpeg",
            "file_size": 1024000
        }
    )
    
    print_result("POST /receipts/request-upload", response.status_code, 
                response.status_code == 200,
                response.json() if response.status_code == 200 else None)
    
    if response.status_code == 200:
        result = response.json().get('data', {})
        receipt_id = result.get('receipt_id')
        upload_url = result.get('upload_url')
        
        print(f"    Receipt ID: {receipt_id}")
        print(f"    Upload URL: {upload_url[:60]}...")
        
        # Step 2: Confirm upload
        response = requests.post(
            f"{API_BASE}/receipts/confirm-upload",
            headers=headers,
            json={
                "receipt_id": receipt_id,
                "buyer_id": buyer_id,
                "order_id": order_id
            }
        )
        
        print_result("POST /receipts/confirm-upload", response.status_code, 
                    response.status_code == 201)
        
        return receipt_id
    
    return None

def test_get_receipt(receipt_id):
    """Test getting receipt details"""
    print_section("GET RECEIPT DETAILS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    response = requests.get(
        f"{API_BASE}/receipts/{receipt_id}",
        headers=headers
    )
    
    print_result(f"GET /receipts/{receipt_id}", response.status_code, 
                response.status_code == 200,
                response.json() if response.status_code == 200 else None)

def test_cancel_order(order_id):
    """Test cancelling an order"""
    print_section("CANCEL ORDER (BUYER)")
    
    headers = {"Authorization": f"Bearer {buyer_token}"}
    
    response = requests.patch(
        f"{API_BASE}/orders/{order_id}/cancel",
        headers=headers,
        json={
            "buyer_id": buyer_id,
            "reason": "Test cancellation"
        }
    )
    
    print_result(f"PATCH /orders/{order_id}/cancel", response.status_code, 
                response.status_code == 200,
                response.json() if response.status_code == 200 else None)

def main():
    """Run all order and receipt tests"""
    print_section("COMPREHENSIVE ORDER & RECEIPT TESTING")
    print(f"API Base: {API_BASE}")
    print(f"Vendor ID: {vendor_id}")
    print(f"Buyer ID: {buyer_id}")
    print(f"CEO ID: {ceo_id}")
    
    # Setup
    setup_test_buyer()
    
    # Authenticate vendor
    if not get_vendor_token():
        print("\n❌ Vendor authentication failed. Stopping tests.")
        return
    
    # Authenticate buyer
    if not get_buyer_token_via_webhook():
        print("\n❌ Buyer authentication failed. Stopping tests.")
        return
    
    # Test order lifecycle
    order_id = test_create_order()
    
    if order_id:
        test_get_order(order_id)
        test_list_orders()
        test_confirm_order(order_id)
        
        # Test receipt upload
        receipt_id = test_receipt_upload_flow(order_id)
        
        if receipt_id:
            test_get_receipt(receipt_id)
        
        # Test cancellation (create another order first)
        print("\n" + "="*70)
        print(" TESTING ORDER CANCELLATION")
        print("="*70)
        cancel_order_id = test_create_order()
        if cancel_order_id:
            test_cancel_order(cancel_order_id)
    
    print_section("ORDER & RECEIPT TESTING COMPLETE")

if __name__ == "__main__":
    main()
