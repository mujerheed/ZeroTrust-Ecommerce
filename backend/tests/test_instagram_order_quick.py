#!/usr/bin/env python3
"""
Quick Instagram Order Test - Inject OTP approach
"""

import requests
import json
import boto3
from hashlib import sha256
import time
from datetime import datetime

API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
VENDOR_PHONE = "+2348133336318"
VENDOR_ID = "ceo_test_001"
IG_BUYER_ID = "ig_1234567890"
TEST_OTP = "Test@123"

print("="*70)
print(" INSTAGRAM ORDER NOTIFICATION TEST")
print("="*70)

# Step 1: Clean OTPs
print("\n1. Cleaning OTPs...")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
otps_table = dynamodb.Table('TrustGuard-OTPs-dev')

response_query = otps_table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(VENDOR_ID)
)
for item in response_query.get('Items', []):
    otps_table.delete_item(Key={
        'user_id': item['user_id'],
        'request_id': item['request_id']
    })
print("   ✓ OTPs cleaned")

# Step 2: Request vendor login
print("\n2. Requesting vendor login...")
resp = requests.post(f"{API_BASE}/auth/vendor/login", json={"phone": VENDOR_PHONE})
print(f"   Status: {resp.status_code}")

# Step 3: Inject test OTP
print("\n3. Injecting test OTP...")
otp_hash = sha256(TEST_OTP.encode()).hexdigest()
otps_table.put_item(Item={
    'user_id': VENDOR_ID,
    'request_id': f'req_{int(time.time())}_instagram_test',
    'otp_hash': otp_hash,
    'role': 'Vendor',
    'expires_at': int(datetime.now().timestamp()) + 300,
    'created_at': datetime.now().isoformat(),
    'attempts': 0
})
print(f"   ✓ OTP injected: {TEST_OTP}")
time.sleep(1)

# Step 4: Verify OTP
print("\n4. Verifying OTP...")
resp = requests.post(
    f"{API_BASE}/auth/verify-otp",
    json={"user_id": VENDOR_ID, "otp": TEST_OTP}
)
print(f"   Status: {resp.status_code}")

if resp.status_code == 200:
    token = resp.json()['data']['token']
    print(f"   ✓ Got token")
    
    # Step 5: Create order for Instagram buyer
    print("\n5. Creating order for Instagram buyer...")
    order_data = {
        "buyer_id": IG_BUYER_ID,
        "items": [
            {"name": "iPhone 15 Pro", "quantity": 1, "price": 1200000},
            {"name": "AirPods Pro", "quantity": 1, "price": 180000}
        ],
        "notes": "🎉 Instagram order - testing Instagram DM notification!"
    }
    
    resp = requests.post(
        f"{API_BASE}/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 201:
        data = resp.json()['data']
        print(f"\n   ✓ SUCCESS!")
        print(f"   Order ID: {data['order_id']}")
        print(f"   Total: ₦{data['total_amount']:,}")
        print(f"   Notification sent: {data.get('notification_sent', False)}")
        
        # Check logs
        print("\n6. Checking CloudWatch logs for Instagram notification...")
        import subprocess
        result = subprocess.run([
            'aws', 'logs', 'tail',
            '/aws/lambda/TrustGuard-OrderService-dev',
            '--since', '1m',
            '--region', 'us-east-1'
        ], capture_output=True, text=True)
        
        for line in result.stdout.split('\n'):
            if 'instagram' in line.lower() or ('notification' in line.lower() and 'ig_' in line):
                print(f"   {line}")
        
    else:
        print(f"   ✗ Failed: {resp.text}")
else:
    print(f"   ✗ OTP verification failed: {resp.text}")

print("\n" + "="*70)
print(" TEST COMPLETE")
print("="*70)
