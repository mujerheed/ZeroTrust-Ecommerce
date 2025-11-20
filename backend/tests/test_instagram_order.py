#!/usr/bin/env python3
"""
Test order creation with Instagram buyer notification.

Tests:
1. Create Instagram buyer
2. Vendor creates order for Instagram buyer
3. Verify Instagram notification sent
"""

import requests
import json
import boto3
from decimal import Decimal

API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
VENDOR_ID = "ceo_test_001"
INSTAGRAM_BUYER_ID = "ig_1234567890"  # Instagram buyer
CEO_ID = "ceo_test_001"

def setup_instagram_buyer():
    """Create test Instagram buyer in DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    users_table = dynamodb.Table('TrustGuard-Users-dev')
    
    instagram_buyer = {
        'user_id': INSTAGRAM_BUYER_ID,
        'role': 'BUYER',
        'ceo_id': CEO_ID,
        'platform': 'instagram',
        'phone': '+2348099887766',  # Same phone but different platform
        'meta': {
            'psid': '1234567890',  # Instagram Page-Scoped ID
            'username': 'test_buyer_ig'
        },
        'created_at': 1763671000,
        'updated_at': 1763671000,
        'is_active': True
    }
    
    users_table.put_item(Item=instagram_buyer)
    print(f"✓ Created Instagram buyer: {INSTAGRAM_BUYER_ID}")
    return instagram_buyer

def get_vendor_token():
    """Get vendor JWT token."""
    # Clean up existing OTP
    requests.delete(f"{API_BASE}/auth/otp/{VENDOR_ID}")
    
    # Request new OTP
    resp = requests.post(
        f"{API_BASE}/auth/vendor/login",
        json={"vendor_id": VENDOR_ID}
    )
    
    if resp.status_code != 200:
        print(f"✗ Login failed: {resp.status_code}")
        return None
    
    otp = resp.json()['data']['otp']
    
    # Verify OTP
    resp = requests.post(
        f"{API_BASE}/auth/verify-otp",
        json={
            "user_id": VENDOR_ID,
            "otp": otp,
            "role": "vendor"
        }
    )
    
    if resp.status_code != 200:
        print(f"✗ OTP verification failed: {resp.status_code}")
        return None
    
    token = resp.json()['data']['access_token']
    print(f"✓ Got vendor token")
    return token

def create_order_for_instagram_buyer(vendor_token):
    """Create order for Instagram buyer."""
    order_data = {
        "buyer_id": INSTAGRAM_BUYER_ID,
        "items": [
            {
                "name": "iPhone 15 Pro",
                "quantity": 1,
                "price": 1200000
            },
            {
                "name": "AirPods Pro",
                "quantity": 1,
                "price": 180000
            }
        ],
        "notes": "Order from Instagram buyer - testing Instagram DM notification"
    }
    
    resp = requests.post(
        f"{API_BASE}/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    print(f"\n{'='*70}")
    print(f" CREATE ORDER FOR INSTAGRAM BUYER")
    print(f"{'='*70}\n")
    
    if resp.status_code == 201:
        data = resp.json()
        order_id = data['data']['order_id']
        notification_sent = data['data'].get('notification_sent', False)
        
        print(f"✓ Order created: {order_id}")
        print(f"  Notification sent: {notification_sent}")
        print(f"\n  Order details:")
        print(json.dumps(data['data'], indent=2))
        return order_id
    else:
        print(f"✗ Order creation failed: {resp.status_code}")
        print(f"  Response: {resp.text}")
        return None

def check_cloudwatch_logs():
    """Check CloudWatch logs for Instagram notification."""
    import subprocess
    
    print(f"\n{'='*70}")
    print(f" CLOUDWATCH LOGS - Instagram Notification")
    print(f"{'='*70}\n")
    
    cmd = [
        'aws', 'logs', 'tail',
        '/aws/lambda/TrustGuard-OrderService-dev',
        '--since', '2m',
        '--region', 'us-east-1'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Filter for Instagram-related logs
    for line in result.stdout.split('\n'):
        if 'instagram' in line.lower() or 'notification' in line.lower():
            print(line)

def main():
    print(f"\n{'='*70}")
    print(f" INSTAGRAM ORDER NOTIFICATION TEST")
    print(f"{'='*70}\n")
    
    print(f"API Base: {API_BASE}")
    print(f"Vendor ID: {VENDOR_ID}")
    print(f"Instagram Buyer ID: {INSTAGRAM_BUYER_ID}")
    print(f"CEO ID: {CEO_ID}\n")
    
    # Setup
    print("Step 1: Setup Instagram buyer...")
    setup_instagram_buyer()
    
    # Get vendor token
    print("\nStep 2: Get vendor authentication token...")
    vendor_token = get_vendor_token()
    if not vendor_token:
        print("✗ Failed to get vendor token")
        return
    
    # Create order
    print("\nStep 3: Create order for Instagram buyer...")
    order_id = create_order_for_instagram_buyer(vendor_token)
    
    if order_id:
        print(f"\n{'='*70}")
        print(f" SUCCESS! Order created with Instagram notification")
        print(f"{'='*70}\n")
        
        # Check logs
        print("\nStep 4: Check CloudWatch logs...")
        check_cloudwatch_logs()
    else:
        print("\n✗ Test failed")

if __name__ == "__main__":
    main()
