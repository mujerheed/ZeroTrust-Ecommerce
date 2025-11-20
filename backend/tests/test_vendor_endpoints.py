#!/usr/bin/env python3
"""
Comprehensive Vendor Service Endpoint Testing
Tests all vendor endpoints systematically with consistent naming
"""

import requests
import json
import boto3
from datetime import datetime
from hashlib import sha256

# Consistent variable naming
API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
vendor_phone = "+2348133336318"  # Test vendor phone (same as CEO - multi-role user)
vendor_token = None
vendor_id = "ceo_test_001"  # Multi-role user (both CEO and Vendor)

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
    """Login as Vendor and get token"""
    global vendor_token
    
    print_section("VENDOR AUTHENTICATION")
    
    # Clean old OTPs first
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    otps_table = dynamodb.Table('TrustGuard-OTPs-dev')
    
    response_query = otps_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(vendor_id)
    )
    deleted_count = 0
    for item in response_query.get('Items', []):
        otps_table.delete_item(Key={
            'user_id': item['user_id'],
            'request_id': item['request_id']
        })
        deleted_count += 1
    print(f"    Cleaned {deleted_count} old OTPs")
    
    # Request OTP
    response = requests.post(
        f"{API_BASE}/auth/vendor/login",
        json={"phone": vendor_phone}
    )
    print_result("POST /auth/vendor/login", response.status_code, response.status_code == 200)
    
    if response.status_code != 200:
        print(f"    Error: {response.text}")
        return False
    
    # Inject test OTP with request_id that sorts AFTER any auto-generated ones
    test_otp = "Test@123"  # 8-char vendor OTP
    otp_hash = sha256(test_otp.encode()).hexdigest()
    
    # Use timestamp + zzz to ensure it sorts last
    import time
    otps_table.put_item(Item={
        'user_id': vendor_id,
        'request_id': f'req_{int(time.time())}_zzztest',  # High sort value
        'otp_hash': otp_hash,
        'role': 'Vendor',
        'expires_at': int(datetime.now().timestamp()) + 300,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    })
    print(f"    Injected test OTP: {test_otp}")
    
    # Small delay to ensure OTP is written
    time.sleep(0.5)
    
    # Verify OTP
    response = requests.post(
        f"{API_BASE}/auth/verify-otp",
        json={
            "user_id": vendor_id,
            "otp": test_otp
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        vendor_token = result.get('data', {}).get('token')
        print_result("POST /auth/verify-otp", response.status_code, True, 
                    {"token_length": len(vendor_token) if vendor_token else 0})
        return True
    else:
        print_result("POST /auth/verify-otp", response.status_code, False)
        print(f"    Error: {response.text}")
        return False

def test_vendor_dashboard():
    """Test vendor dashboard endpoint"""
    print_section("VENDOR DASHBOARD")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    response = requests.get(f"{API_BASE}/vendor/dashboard", headers=headers)
    print_result("GET /vendor/dashboard", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)

def test_vendor_orders():
    """Test vendor order management endpoints"""
    print_section("VENDOR ORDER MANAGEMENT")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Get all orders
    response = requests.get(f"{API_BASE}/vendor/orders", headers=headers)
    print_result("GET /vendor/orders", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Search orders
    response = requests.get(
        f"{API_BASE}/vendor/orders/search",
        headers=headers,
        params={"query": "test", "limit": 10}
    )
    print_result("GET /vendor/orders/search", response.status_code, 
                response.status_code == 200)

def test_vendor_receipts():
    """Test vendor receipt endpoints"""
    print_section("VENDOR RECEIPT MANAGEMENT")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Get pending receipts
    response = requests.get(f"{API_BASE}/vendor/receipts/pending", headers=headers)
    print_result("GET /vendor/receipts/pending", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)

def test_vendor_preferences():
    """Test vendor preferences endpoints"""
    print_section("VENDOR PREFERENCES")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Get preferences
    response = requests.get(f"{API_BASE}/vendor/preferences", headers=headers)
    print_result("GET /vendor/preferences", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Update preferences
    response = requests.put(
        f"{API_BASE}/vendor/preferences",
        headers=headers,
        json={
            "notification_email": "vendor@example.com",
            "sms_alerts": True,
            "auto_approve_threshold": 50000
        }
    )
    print_result("PUT /vendor/preferences", response.status_code, 
                response.status_code == 200)

def test_vendor_notifications():
    """Test vendor notification endpoints"""
    print_section("VENDOR NOTIFICATIONS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Get unread notifications
    response = requests.get(f"{API_BASE}/vendor/notifications/unread", headers=headers)
    print_result("GET /vendor/notifications/unread", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)

def test_vendor_stats():
    """Test vendor statistics endpoint"""
    print_section("VENDOR STATISTICS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    response = requests.get(f"{API_BASE}/vendor/stats", headers=headers)
    print_result("GET /vendor/stats", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)

def test_vendor_analytics():
    """Test vendor analytics endpoints"""
    print_section("VENDOR ANALYTICS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Orders by day
    response = requests.get(
        f"{API_BASE}/vendor/analytics/orders-by-day",
        headers=headers,
        params={"days": 7}
    )
    print_result("GET /vendor/analytics/orders-by-day", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)

def main():
    """Run all vendor endpoint tests"""
    print_section("COMPREHENSIVE VENDOR ENDPOINT TESTING")
    print(f"API Base: {API_BASE}")
    print(f"Vendor Phone: {vendor_phone}")
    print(f"Vendor ID: {vendor_id}")
    
    # Step 1: Authenticate
    if not get_vendor_token():
        print("\n❌ Vendor authentication failed. Stopping tests.")
        return
    
    # Step 2: Test all vendor endpoints
    test_vendor_dashboard()
    test_vendor_orders()
    test_vendor_receipts()
    test_vendor_preferences()
    test_vendor_notifications()
    test_vendor_stats()
    test_vendor_analytics()
    
    print_section("VENDOR ENDPOINT TESTING COMPLETE")

if __name__ == "__main__":
    main()
