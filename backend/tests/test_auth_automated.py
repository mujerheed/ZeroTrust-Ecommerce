#!/usr/bin/env python3
"""
Automated authentication flow test with direct DynamoDB OTP injection.
This bypasses OTP delivery and allows automated testing.
"""

import os
import sys
import json
import hashlib
import time
import boto3
import requests
from dotenv import load_dotenv
from typing import Dict, Any

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def inject_test_otp(user_id: str, otp: str, role: str) -> bool:
    """
    Inject a known OTP directly into DynamoDB for testing.
    This simulates the OTP delivery without actually sending it.
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('TrustGuard-OTPs-dev')
        
        # First, delete any existing test OTPs to prevent conflicts
        # Query all items for this user
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        
        # Delete all test OTP entries (those with _zzztest suffix)
        deleted_count = 0
        for item in response.get('Items', []):
            if 'zzztest' in item.get('request_id', ''):
                table.delete_item(
                    Key={
                        'user_id': user_id,
                        'request_id': item['request_id']
                    }
                )
                deleted_count += 1
        
        if deleted_count > 0:
            print_info(f"Cleaned up {deleted_count} old test OTP(s)")
        
        # Hash the OTP (same as otp_manager.py does)
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        
        now = int(time.time())
        # Use consistent suffix to ensure test OTP is retrieved
        request_id = f"req_9999999999_zzztest"
        
        item = {
            'user_id': user_id,
            'request_id': request_id,
            'otp_hash': otp_hash,
            'role': role,
            'delivery_method': 'test',
            'attempts': 0,
            'created_at': now,
            'expires_at': now + 300,  # 5 minutes TTL
            'locked_until': 0
        }
        
        table.put_item(Item=item)
        print_success(f"Test OTP '{otp}' injected for {user_id}")
        return True
        
    except Exception as e:
        print_error(f"Failed to inject OTP: {str(e)}")
        return False

def test_ceo_flow(api_base: str, phone: str) -> bool:
    """Test CEO authentication flow with automated OTP injection."""
    print_header("CEO Authentication Flow (Automated)")
    
    # Step 1: Request OTP (this will create a user_id)
    print_info("Step 1: Requesting CEO OTP")
    response = requests.post(
        f"{api_base}/auth/ceo/login",
        json={"contact": phone},
        timeout=30
    )
    
    print_info(f"Status: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code != 200:
        print_error("CEO login request failed")
        return False
    
    data = response.json()
    ceo_id = data.get('data', {}).get('ceo_id')
    
    if not ceo_id:
        print_error("No ceo_id returned")
        return False
    
    print_success(f"OTP request successful, ceo_id: {ceo_id}")
    
    # Step 2: Inject known test OTP
    print_info("Step 2: Injecting test OTP into DynamoDB")
    test_otp = "123@45"  # 6-char CEO OTP with symbol
    
    if not inject_test_otp(ceo_id, test_otp, "CEO"):
        return False
    
    # Wait a moment for DynamoDB consistency
    time.sleep(1)
    
    # Step 3: Verify OTP
    print_info("Step 3: Verifying OTP")
    response = requests.post(
        f"{api_base}/auth/verify-otp",
        json={"user_id": ceo_id, "otp": test_otp},
        timeout=30
    )
    
    print_info(f"Status: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code != 200:
        print_error("OTP verification failed")
        return False
    
    data = response.json()
    token = data.get('data', {}).get('token')
    role = data.get('data', {}).get('role')
    
    if not token:
        print_error("No JWT token returned")
        return False
    
    print_success(f"Authentication successful! Role: {role}")
    print_info(f"JWT Token: {token[:50]}...")
    
    return True

def test_vendor_flow(api_base: str, phone: str) -> bool:
    """Test Vendor authentication flow with automated OTP injection."""
    print_header("Vendor Authentication Flow (Automated)")
    
    # Step 1: Request OTP
    print_info("Step 1: Requesting Vendor OTP")
    response = requests.post(
        f"{api_base}/auth/vendor/login",
        json={"phone": phone},
        timeout=30
    )
    
    print_info(f"Status: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code != 200:
        print_error("Vendor login request failed")
        return False
    
    data = response.json()
    vendor_id = data.get('data', {}).get('vendor_id')
    
    if not vendor_id:
        print_error("No vendor_id returned")
        return False
    
    print_success(f"OTP request successful, vendor_id: {vendor_id}")
    
    # Step 2: Inject known test OTP
    print_info("Step 2: Injecting test OTP into DynamoDB")
    test_otp = "Test@123"  # 8-char Vendor OTP
    
    if not inject_test_otp(vendor_id, test_otp, "Vendor"):
        return False
    
    # Wait a moment for DynamoDB consistency
    time.sleep(1)
    
    # Step 3: Verify OTP
    print_info("Step 3: Verifying OTP")
    response = requests.post(
        f"{api_base}/auth/verify-otp",
        json={"user_id": vendor_id, "otp": test_otp},
        timeout=30
    )
    
    print_info(f"Status: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code != 200:
        print_error("OTP verification failed")
        return False
    
    data = response.json()
    token = data.get('data', {}).get('token')
    role = data.get('data', {}).get('role')
    
    if not token:
        print_error("No JWT token returned")
        return False
    
    print_success(f"Authentication successful! Role: {role}")
    print_info(f"JWT Token: {token[:50]}...")
    
    return True

def main():
    # Load environment
    load_dotenv()
    
    api_base = os.getenv('API_BASE_URL', 'https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod')
    ceo_phone = os.getenv('TEST_CEO_PHONE', '+2348133336318')
    vendor_phone = os.getenv('TEST_VENDOR_PHONE', '+2348133336318')
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║        TrustGuard Automated Authentication Test                           ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    print_info(f"API Base URL: {api_base}")
    print_info(f"CEO Phone: {ceo_phone}")
    print_info(f"Vendor Phone: {vendor_phone}")
    
    # Test CEO flow
    ceo_success = test_ceo_flow(api_base, ceo_phone)
    
    # Test Vendor flow
    vendor_success = test_vendor_flow(api_base, vendor_phone)
    
    # Summary
    print_header("Test Summary")
    if ceo_success:
        print_success("CEO authentication flow: PASSED")
    else:
        print_error("CEO authentication flow: FAILED")
    
    if vendor_success:
        print_success("Vendor authentication flow: PASSED")
    else:
        print_error("Vendor authentication flow: FAILED")
    
    if ceo_success and vendor_success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed!{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
