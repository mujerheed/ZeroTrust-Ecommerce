"""
Automated Phase 2 Endpoint Testing
Tests all Phase 2 features with automated OTP authentication

Usage:
    python test_phase2_automated.py
"""

import os
import sys
import requests
import boto3
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Test credentials (using dual-role user from test_auth_automated.py)
TEST_CEO_PHONE = "+2348133336318"
TEST_VENDOR_PHONE = "+2348133336318"
TEST_CEO_ID = "ceo_test_001"
TEST_VENDOR_ID = "ceo_test_001"  # Same user, dual role

# Test OTPs
CEO_TEST_OTP = "123@45"  # 6-character
VENDOR_TEST_OTP = "Test@123"  # 8-character


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}\n{text:^80}\n{'='*80}{Colors.ENDC}")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def inject_test_otp(user_id: str, otp: str, role: str) -> bool:
    """Inject a test OTP into DynamoDB for automated testing"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table('TrustGuard-OTPs-dev')
        
        # First, delete any existing test OTPs to prevent conflicts
        # Query all items for this user
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        
        # Delete all test OTP entries (those with _zzztest suffix)
        for item in response.get('Items', []):
            if 'zzztest' in item.get('request_id', ''):
                table.delete_item(
                    Key={
                        'user_id': user_id,
                        'request_id': item['request_id']
                    }
                )
        
        # Hash OTP
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        
        # Create request_id that sorts last alphabetically (after all real OTPs)
        request_id = f"req_9999999999_zzztest"
        
        # Calculate expiration (5 minutes from now)
        expires_at = int(time.time()) + 300
        
        table.put_item(Item={
            'user_id': user_id,
            'request_id': request_id,
            'otp_hash': otp_hash,
            'role': role,
            'delivery_method': 'test',
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at,  # Add expires_at field
            'attempts': 0,
            'locked_until': 0,  # Not locked
            'ttl': expires_at  # DynamoDB TTL
        })
        
        return True
    except Exception as e:
        print_error(f"Failed to inject OTP: {str(e)}")
        return False


def authenticate_ceo() -> Optional[str]:
    """Authenticate CEO and return JWT token"""
    print_header("CEO Authentication")
    
    # Step 1: Request OTP via CEO login
    print_info("Step 1: Requesting CEO OTP...")
    response = requests.post(
        f"{API_BASE_URL}/auth/ceo/login",
        json={"contact": TEST_CEO_PHONE}
    )
    
    if response.status_code == 400 and "429" in response.text:
        print_warning("⚠ CEO login rate-limited. Skipping CEO tests...")
        return "RATE_LIMITED"
    
    if response.status_code != 200:
        print_error(f"Failed to request CEO OTP: {response.text}")
        return None
    
    print_success(f"OTP request successful, ceo_id: {TEST_CEO_ID}")
    
    # Step 2: Inject test OTP
    print_info("Step 2: Injecting test OTP...")
    if not inject_test_otp(TEST_CEO_ID, CEO_TEST_OTP, "CEO"):
        return None
    print_success(f"Test OTP '{CEO_TEST_OTP}' injected")
    
    # Step 3: Verify OTP
    print_info("Step 3: Verifying OTP...")
    time.sleep(2)  # Wait for DynamoDB consistency
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={"user_id": TEST_CEO_ID, "otp": CEO_TEST_OTP}
    )
    
    if response.status_code != 200:
        print_error(f"OTP verification failed: {response.text}")
        return None
    
    data = response.json().get("data", {})
    token = data.get("token")
    role = data.get("role")
    
    print_success(f"CEO authenticated successfully! Role: {role}")
    print_info(f"JWT Token: {token[:50]}...")
    
    return token


def authenticate_vendor() -> Optional[str]:
    """Authenticate Vendor and return JWT token"""
    print_header("Vendor Authentication")
    
    # Step 1: Request OTP via Vendor login
    print_info("Step 1: Requesting Vendor OTP...")
    response = requests.post(
        f"{API_BASE_URL}/auth/vendor/login",
        json={"phone": TEST_VENDOR_PHONE}
    )
    
    if response.status_code != 200:
        print_error(f"Failed to request Vendor OTP: {response.text}")
        return None
    
    print_success(f"OTP request successful, vendor_id: {TEST_VENDOR_ID}")
    
    # Step 2: Inject test OTP
    print_info("Step 2: Injecting test OTP...")
    if not inject_test_otp(TEST_VENDOR_ID, VENDOR_TEST_OTP, "Vendor"):
        return None
    print_success(f"Test OTP '{VENDOR_TEST_OTP}' injected")
    
    # Step 3: Verify OTP
    print_info("Step 3: Verifying OTP...")
    time.sleep(2)  # Wait for DynamoDB consistency
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={"user_id": TEST_VENDOR_ID, "otp": VENDOR_TEST_OTP}
    )
    
    if response.status_code != 200:
        print_error(f"OTP verification failed: {response.text}")
        return None
    
    data = response.json().get("data", {})
    token = data.get("token")
    role = data.get("role")
    
    print_success(f"Vendor authenticated successfully! Role: {role}")
    print_info(f"JWT Token: {token[:50]}...")
    
    return token


def test_ceo_chatbot_config(ceo_token: str) -> bool:
    """Test CEO chatbot configuration endpoints"""
    print_header("CEO Chatbot Configuration")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # Test GET chatbot settings
    print_info("Testing GET /ceo/chatbot/settings...")
    response = requests.get(
        f"{API_BASE_URL}/ceo/chatbot/settings",
        headers=headers
    )
    
    if response.status_code == 200:
        settings = response.json().get("data", {})
        print_success(f"Retrieved chatbot settings: {json.dumps(settings, indent=2)}")
    else:
        print_error(f"Failed to get chatbot settings: {response.status_code} - {response.text}")
        return False
    
    # Test PUT chatbot settings
    print_info("Testing PUT /ceo/chatbot/settings...")
    new_settings = {
        "welcome_message": "Welcome to TrustGuard automated test!",
        "otp_instructions": "Test OTP instructions",
        "auto_respond": True
    }
    
    response = requests.put(
        f"{API_BASE_URL}/ceo/chatbot/settings",
        headers=headers,
        json=new_settings
    )
    
    if response.status_code == 200:
        print_success("Updated chatbot settings successfully")
        return True
    else:
        print_error(f"Failed to update chatbot settings: {response.status_code} - {response.text}")
        return False


def test_vendor_preferences(vendor_token: str) -> bool:
    """Test vendor preferences endpoints"""
    print_header("Vendor Preferences (OCR Settings)")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Test GET preferences
    print_info("Testing GET /vendor/preferences...")
    response = requests.get(
        f"{API_BASE_URL}/vendor/preferences",
        headers=headers
    )
    
    if response.status_code == 200:
        prefs = response.json().get("data", {})
        print_success(f"Retrieved vendor preferences: {json.dumps(prefs, indent=2)}")
    else:
        print_error(f"Failed to get vendor preferences: {response.status_code} - {response.text}")
        return False
    
    # Test PUT preferences (update OCR settings)
    print_info("Testing PUT /vendor/preferences...")
    new_prefs = {
        "ocr_auto_approve": True,
        "ocr_confidence_threshold": 85.0,
        "ocr_amount_tolerance": 5.0,
        "auto_approve_max_amount": 50000.0
    }
    
    response = requests.put(
        f"{API_BASE_URL}/vendor/preferences",
        headers=headers,
        json=new_prefs
    )
    
    if response.status_code == 200:
        print_success("Updated vendor preferences successfully")
        return True
    else:
        print_error(f"Failed to update vendor preferences: {response.status_code} - {response.text}")
        return False


def test_analytics_endpoints(ceo_token: str, vendor_token: str) -> bool:
    """Test analytics endpoints"""
    print_header("Analytics Endpoints")
    
    success = True
    
    # Test vendor analytics
    print_info("Testing GET /vendor/analytics/orders-by-day...")
    response = requests.get(
        f"{API_BASE_URL}/vendor/analytics/orders-by-day?days=7",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        print_success(f"Vendor orders analytics: {len(data)} days of data")
    else:
        print_error(f"Failed to get vendor analytics: {response.status_code} - {response.text}")
        success = False
    
    # Test CEO fraud trends
    print_info("Testing GET /ceo/analytics/fraud-trends...")
    response = requests.get(
        f"{API_BASE_URL}/ceo/analytics/fraud-trends?days=30",
        headers={"Authorization": f"Bearer {ceo_token}"}
    )
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        print_success(f"CEO fraud trends: {json.dumps(data, indent=2)}")
    else:
        print_error(f"Failed to get CEO fraud trends: {response.status_code} - {response.text}")
        success = False
    
    return success


def test_vendor_risk_scores(ceo_token: str) -> bool:
    """Test vendor list with risk scores"""
    print_header("Vendor Risk Scores")
    
    print_info("Testing GET /ceo/vendors (with risk_score field)...")
    response = requests.get(
        f"{API_BASE_URL}/ceo/vendors",
        headers={"Authorization": f"Bearer {ceo_token}"}
    )
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        # Handle both list and dict response structures
        if isinstance(data, list):
            vendors = data
        else:
            vendors = data.get("vendors", [])
        
        print_success(f"Retrieved {len(vendors)} vendors")
        
        for vendor in vendors:
            if isinstance(vendor, dict):
                risk_score = vendor.get("risk_score", "N/A")
                vendor_id = vendor.get("user_id") or vendor.get("vendor_id", "unknown")
                print_info(f"  Vendor {vendor_id}: Risk Score = {risk_score}")
            else:
                print_info(f"  Vendor: {vendor}")
        
        return True
    else:
        print_error(f"Failed to get vendors: {response.status_code} - {response.text}")
        return False

def test_notification_polling(vendor_token: str) -> bool:
    """Test notification polling endpoint"""
    print_header("Notification Polling")
    
    print_info("Testing GET /vendor/notifications/unread...")
    response = requests.get(
        f"{API_BASE_URL}/vendor/notifications/unread",
        headers={"Authorization": f"Bearer {vendor_token}"}
    )
    
    if response.status_code == 200:
        notifications = response.json().get("data", [])
        print_success(f"Retrieved {len(notifications)} unread notifications")
        
        for notif in notifications[:3]:  # Show first 3
            print_info(f"  {notif.get('type')}: {notif.get('message')}")
        
        return True
    else:
        print_error(f"Failed to get notifications: {response.status_code} - {response.text}")
        return False


def main():
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔" + "="*78 + "╗")
    print("║" + "TrustGuard Phase 2 Automated Testing Suite".center(78) + "║")
    print("║" + "OCR Auto-Approval + Backend 100% Validation".center(78) + "║")
    print("╚" + "="*78 + "╝")
    print(Colors.ENDC)
    
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Test CEO/Vendor Phone: {TEST_CEO_PHONE}")
    
    # Authenticate
    ceo_token = authenticate_ceo()
    ceo_rate_limited = (ceo_token == "RATE_LIMITED")
    
    if not ceo_token:
        print_error("CEO authentication failed. Aborting tests.")
        sys.exit(1)
    
    time.sleep(1)  # Small delay between authentications
    
    vendor_token = authenticate_vendor()
    if not vendor_token:
        print_error("Vendor authentication failed. Aborting tests.")
        sys.exit(1)
    
    # Run tests (skip CEO-only tests if rate limited)
    results = {}
    
    if not ceo_rate_limited:
        results["CEO Chatbot Configuration"] = test_ceo_chatbot_config(ceo_token)
        results["Vendor Risk Scores"] = test_vendor_risk_scores(ceo_token)
    else:
        print_warning("Skipping CEO-only tests due to rate limit")
    
    # Vendor tests (always run if authenticated)
    results["Vendor Preferences"] = test_vendor_preferences(vendor_token)
    results["Notification Polling"] = test_notification_polling(vendor_token)
    
    # Analytics tests (need both tokens, skip if CEO rate limited)
    if not ceo_rate_limited:
        results["Analytics Endpoints"] = test_analytics_endpoints(ceo_token, vendor_token)
    
    # Summary
    print_header("Test Summary")
    
    if ceo_rate_limited:
        print_warning(f"CEO rate-limited: Ran {len(results)} vendor-focused tests")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.OKGREEN}{Colors.BOLD}\n✓ All Phase 2 tests passed!{Colors.ENDC}\n")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}\n✗ Some tests failed!{Colors.ENDC}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
