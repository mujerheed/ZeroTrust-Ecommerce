#!/usr/bin/env python3
"""Debug Vendor OTP Verification Issue"""

import boto3
import hashlib
import time
import requests
from boto3.dynamodb.conditions import Key

API_BASE = 'https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod'
AWS_REGION = 'us-east-1'
USER_ID = 'ceo_test_001'
VENDOR_OTP = 'Test@123'

print("="*70)
print("Vendor OTP Verification Debug")
print("="*70)

# Step 1: Clean ALL OTPs for this user
print("\n[1] Cleaning ALL OTPs for user...")
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table('TrustGuard-OTPs-dev')

response = table.query(KeyConditionExpression=Key('user_id').eq(USER_ID))
deleted = 0
for item in response.get('Items', []):
    table.delete_item(Key={'user_id': USER_ID, 'request_id': item['request_id']})
    deleted += 1
print(f"   Deleted {deleted} OTP(s)")

# Step 2: Request new Vendor OTP
print("\n[2] Requesting new Vendor OTP...")
response = requests.post(
    f'{API_BASE}/auth/vendor/login',
    json={'phone': '+2348133336318'},
    timeout=30
)
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   ERROR: {response.text}")
    exit(1)

# Step 3: Inject test OTP (with correct hash)
print("\n[3] Injecting test Vendor OTP...")
otp_hash = hashlib.sha256(VENDOR_OTP.encode()).hexdigest()
print(f"   OTP: {VENDOR_OTP}")
print(f"   Hash: {otp_hash}")

now = int(time.time())
request_id = 'req_9999999999_zzztest'

table.put_item(Item={
    'user_id': USER_ID,
    'request_id': request_id,
    'otp_hash': otp_hash,
    'role': 'Vendor',
    'delivery_method': 'test',
    'attempts': 0,
    'created_at': now,
    'expires_at': now + 300,
    'locked_until': 0,
    'ttl': now + 300
})
print(f"   Injected test OTP with request_id: {request_id}")

# Step 4: Verify database state
print("\n[4] Verifying database state...")
time.sleep(2)  # Wait for consistency

db_response = table.query(
    KeyConditionExpression=Key('user_id').eq(USER_ID),
    ScanIndexForward=False
)

print(f"   Total OTPs: {len(db_response['Items'])}")
for idx, item in enumerate(db_response['Items'][:3]):
    print(f"   [{idx}] {item['request_id']}: role={item.get('role')}, hash={item['otp_hash'][:20]}..., expires={item.get('expires_at')}")

# Step 5: Verify via API
print("\n[5] Verifying OTP via API...")
response = requests.post(
    f'{API_BASE}/auth/verify-otp',
    json={'user_id': USER_ID, 'otp': VENDOR_OTP},
    timeout=30
)

print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ SUCCESS!")
    data = response.json()
    print(f"   Token: {data.get('data', {}).get('token', 'N/A')[:50]}...")
    print(f"   Role: {data.get('data', {}).get('role')}")
else:
    print(f"   ✗ FAILED!")
    print(f"   Response: {response.text}")
    
    # Additional debug: check if OTP is still there
    print("\n[6] Checking if OTP still exists after failed verification...")
    db_response2 = table.query(
        KeyConditionExpression=Key('user_id').eq(USER_ID),
        ScanIndexForward=False,
        Limit=1
    )
    if db_response2['Items']:
        item = db_response2['Items'][0]
        print(f"   OTP found: {item['request_id']}, attempts={item.get('attempts', 0)}")
    else:
        print(f"   No OTP found (might have been deleted)")

print("\n" + "="*70)
