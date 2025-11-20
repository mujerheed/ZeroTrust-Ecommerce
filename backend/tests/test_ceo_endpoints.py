#!/usr/bin/env python3
"""
Comprehensive CEO Service Endpoint Testing
Tests all CEO endpoints systematically with consistent naming
"""

import requests
import json
from datetime import datetime

# Consistent variable naming
API_BASE = "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod"
ceo_email = "test.ceo@trustguard.com"  # Test CEO email
ceo_phone = "+2348133336318"  # Test CEO phone
ceo_token = None
vendor_id = "vendor_test_001"  # Test vendor ID

def print_section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")

def print_result(endpoint, status_code, success, data=None):
    status_icon = "✓" if success else "✗"
    print(f"[{status_icon}] {endpoint}: {status_code}")
    if data:
        print(f"    Data: {json.dumps(data, indent=4)[:200]}...")

def get_ceo_token():
    """Login as CEO and get token"""
    global ceo_token
    
    print_section("CEO AUTHENTICATION")
    
    # Request OTP
    response = requests.post(
        f"{API_BASE}/auth/ceo/login",
        json={"contact": ceo_email}
    )
    print_result("POST /auth/ceo/login", response.status_code, response.status_code == 200)
    
    if response.status_code != 200:
        return False
    
    # Get ceo_id from login response
    ceo_id = response.json().get("data", {}).get("ceo_id")
    if not ceo_id:
        print("    ❌ No ceo_id in response")
        return False
    
    print(f"    CEO ID: {ceo_id}")
    
    # Inject test OTP (in real scenario, CEO would receive OTP via SMS)
    import boto3
    from hashlib import sha256
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    otps_table = dynamodb.Table('TrustGuard-OTPs-dev')
    
    test_otp = "Test@1"  # 6-char CEO OTP with symbol
    otp_hash = sha256(test_otp.encode()).hexdigest()
    
    # Inject test OTP with correct schema (user_id=ceo_id, not email)
    otps_table.put_item(Item={
        'user_id': ceo_id,  # Partition key - use ceo_id NOT email
        'request_id': 'req_9999999999_zzztest_ceo',  # Sort key - use high sort value
        'otp_hash': otp_hash,
        'role': 'CEO',
        'expires_at': int(datetime.now().timestamp()) + 300,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    })
    print(f"    Injected test OTP for ceo_id: {ceo_id}")
    
    # Verify OTP using ceo_id (not email!)
    response = requests.post(
        f"{API_BASE}/auth/verify-otp",
        json={
            "user_id": ceo_id,  # Use ceo_id NOT email
            "otp": test_otp
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        ceo_token = result.get('data', {}).get('token')
        print_result("POST /auth/verify-otp/ceo", response.status_code, True, 
                    {"token_length": len(ceo_token) if ceo_token else 0})
        return True
    else:
        print_result("POST /auth/verify-otp/ceo", response.status_code, False)
        return False

def test_ceo_dashboard():
    """Test CEO dashboard endpoint"""
    print_section("CEO DASHBOARD")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    response = requests.get(f"{API_BASE}/ceo/dashboard", headers=headers)
    print_result("GET /ceo/dashboard", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)

def test_ceo_vendors():
    """Test CEO vendor management endpoints"""
    print_section("CEO VENDOR MANAGEMENT")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # List all vendors
    response = requests.get(f"{API_BASE}/ceo/vendors", headers=headers)
    print_result("GET /ceo/vendors", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Create a new vendor
    response = requests.post(
        f"{API_BASE}/ceo/vendors",
        headers=headers,
        json={
            "phone": "+2349988776655",
            "name": "New Test Vendor",
            "email": "vendor@test.com"
        }
    )
    print_result("POST /ceo/vendors", response.status_code, 
                response.status_code == 201)
    
    # Delete vendor (if creation was successful)
    if response.status_code == 201:
        response = requests.delete(
            f"{API_BASE}/ceo/vendors/{vendor_id}",
            headers=headers
        )
        print_result(f"DELETE /ceo/vendors/{vendor_id}", response.status_code, 
                    response.status_code in [200, 404])

def test_ceo_approvals():
    """Test CEO approval workflow endpoints"""
    print_section("CEO APPROVAL WORKFLOWS")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # Get pending approvals (use /approvals endpoint, not /approvals/pending)
    response = requests.get(f"{API_BASE}/ceo/approvals", headers=headers)
    print_result("GET /ceo/approvals", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Request OTP for approval action
    response = requests.post(
        f"{API_BASE}/ceo/approvals/request-otp",
        headers=headers,
        json={"order_id": "test_order_123"}
    )
    print_result("POST /ceo/approvals/request-otp", response.status_code, 
                response.status_code in [200, 404])

def test_ceo_audit_logs():
    """Test CEO audit log endpoints"""
    print_section("CEO AUDIT LOGS")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # Get audit logs
    response = requests.get(f"{API_BASE}/ceo/audit-logs", headers=headers)
    print_result("GET /ceo/audit-logs", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Get filtered audit logs (by vendor)
    response = requests.get(
        f"{API_BASE}/ceo/audit-logs",
        headers=headers,
        params={"vendor_id": vendor_id, "limit": 10}
    )
    print_result("GET /ceo/audit-logs?vendor_id=X", response.status_code, 
                response.status_code == 200)

def test_ceo_analytics():
    """Test CEO analytics endpoints (already tested but re-verify)"""
    print_section("CEO ANALYTICS")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # Fraud trends
    response = requests.get(f"{API_BASE}/ceo/analytics/fraud-trends", headers=headers)
    print_result("GET /ceo/analytics/fraud-trends", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Vendor performance
    response = requests.get(f"{API_BASE}/ceo/analytics/vendor-performance", headers=headers)
    print_result("GET /ceo/analytics/vendor-performance", response.status_code, 
                response.status_code == 200)

def test_ceo_chatbot():
    """Test CEO chatbot configuration (already tested but re-verify)"""
    print_section("CEO CHATBOT CONFIGURATION")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # Get chatbot settings
    response = requests.get(f"{API_BASE}/ceo/chatbot/settings", headers=headers)
    print_result("GET /ceo/chatbot/settings", response.status_code, 
                response.status_code == 200, response.json() if response.status_code == 200 else None)
    
    # Update chatbot settings
    response = requests.put(
        f"{API_BASE}/ceo/chatbot/settings",
        headers=headers,
        json={
            "welcome_message": "Welcome to TrustGuard! 🛡️",
            "tone": "professional",
            "enabled_features": ["order_tracking", "receipt_verification"]
        }
    )
    print_result("PUT /ceo/chatbot/settings", response.status_code, 
                response.status_code == 200)

def main():
    """Run all CEO endpoint tests"""
    print_section("COMPREHENSIVE CEO ENDPOINT TESTING")
    print(f"API Base: {API_BASE}")
    print(f"CEO Email: {ceo_email}")
    print(f"Test Vendor ID: {vendor_id}")
    
    # Step 1: Authenticate
    if not get_ceo_token():
        print("\n❌ CEO authentication failed. Stopping tests.")
        return
    
    # Step 2: Test all CEO endpoints
    test_ceo_dashboard()
    test_ceo_vendors()
    test_ceo_approvals()
    test_ceo_audit_logs()
    test_ceo_analytics()
    test_ceo_chatbot()
    
    print_section("CEO ENDPOINT TESTING COMPLETE")

if __name__ == "__main__":
    main()
