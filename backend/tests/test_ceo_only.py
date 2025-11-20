#!/usr/bin/env python3
"""Quick test for CEO authentication only"""

import requests
import boto3
import hashlib
import time
from boto3.dynamodb.conditions import Key

API_BASE = 'https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod'
CEO_PHONE = '+2348133336318'

print('Testing CEO Authentication Only')
print('='*80)

# Step 1: Request OTP
print('Step 1: Requesting CEO OTP...')
response = requests.post(
    f'{API_BASE}/auth/ceo/login',
    json={'contact': CEO_PHONE},
    timeout=30
)
print(f'Status: {response.status_code}')
data = response.json()
print(f'Response: {data}')
ceo_id = data['data']['ceo_id']
print(f'CEO ID: {ceo_id}')

# Step 2: Inject test OTP
print('\nStep 2: Injecting test OTP...')
test_otp = '123@45'
otp_hash = hashlib.sha256(test_otp.encode()).hexdigest()
print(f'Test OTP: {test_otp}')
print(f'Hash: {otp_hash}')

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('TrustGuard-OTPs-dev')

now = int(time.time())
request_id = f'req_9999999999_zzztest'

table.put_item(Item={
    'user_id': ceo_id,
    'request_id': request_id,
    'otp_hash': otp_hash,
    'role': 'CEO',
    'delivery_method': 'test',
    'attempts': 0,
    'created_at': now,
    'expires_at': now + 300,
    'locked_until': 0
})
print('OTP injected')

# Wait for consistency
time.sleep(1)

# Verify what's in the DB
print('\nVerifying database state...')
db_response = table.query(
    KeyConditionExpression=Key('user_id').eq(ceo_id),
    ScanIndexForward=False,
    Limit=1
)
if db_response['Items']:
    item = db_response['Items'][0]
    print(f"Most recent OTP: request_id={item['request_id']}, role={item['role']}, hash={item['otp_hash'][:16]}...")

# Step 3: Verify OTP
print('\nStep 3: Verifying OTP...')
response = requests.post(
    f'{API_BASE}/auth/verify-otp',
    json={'user_id': ceo_id, 'otp': test_otp},
    timeout=30
)
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')

if response.status_code == 200:
    print('\n✓ CEO authentication PASSED')
else:
    print('\n✗ CEO authentication FAILED')
