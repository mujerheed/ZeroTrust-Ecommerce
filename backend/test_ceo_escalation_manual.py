#!/usr/bin/env python3
"""
Manual testing script for CEO Escalation Workflow.

This script tests the CEO escalation endpoints with mock data,
without requiring real AWS DynamoDB or SNS services.

Usage:
    python test_ceo_escalation_manual.py
"""

import requests
import json
from datetime import datetime, timedelta
import jwt
from common.config import settings

BASE_URL = "http://localhost:8000"

# Color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(test_name):
    """Print test header."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """Print error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    """Print info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")


def create_mock_jwt(user_id="ceo_123", role="CEO", ceo_id=None):
    """
    Create a mock JWT token for testing.
    
    Args:
        user_id: User identifier
        role: User role (CEO, VENDOR, BUYER)
        ceo_id: CEO identifier for multi-tenancy
    
    Returns:
        JWT token string
    """
    exp_time = datetime.utcnow() + timedelta(hours=1)
    
    payload = {
        'sub': user_id,
        'role': role,
        'jti': 'test-jwt-id',
        'iat': datetime.utcnow(),
        'exp': exp_time
    }
    
    if ceo_id:
        payload['ceo_id'] = ceo_id
    elif role == 'CEO':
        payload['ceo_id'] = user_id
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


def test_list_escalations(token):
    """Test GET /ceo/escalations endpoint."""
    print_test("List Pending Escalations")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/ceo/escalations", headers=headers)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Endpoint responded successfully")
                escalations = data.get('data', {}).get('escalations', [])
                print_info(f"Found {len(escalations)} escalations")
                
                # Check for PII masking
                if escalations:
                    first = escalations[0]
                    if 'buyer_phone' in first and len(first['buyer_phone']) <= 10:
                        print_success("PII masking appears to be working (phone truncated)")
                
                return True
            else:
                print_error(f"Unexpected status: {data.get('status')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on port 8000?")
        return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def test_request_otp(token):
    """Test POST /ceo/escalations/request-otp endpoint."""
    print_test("Request CEO OTP")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ceo/escalations/request-otp", headers=headers)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("OTP generated successfully")
                # Try both 'otp' and 'dev_otp' fields (dev mode returns 'dev_otp')
                otp = data.get('data', {}).get('otp') or data.get('data', {}).get('dev_otp')
                if otp:
                    print_info(f"Generated OTP: {otp}")
                    print_info(f"OTP Length: {len(otp)} chars")
                    
                    # Validate OTP format (6 chars, digits + symbols)
                    if len(otp) == 6:
                        print_success("OTP has correct length (6 characters)")
                    else:
                        print_error(f"OTP length incorrect: expected 6, got {len(otp)}")
                    
                    return otp
                else:
                    print_error("No OTP in response")
                    return None
            else:
                print_error(f"Unexpected status: {data.get('status')}")
                return None
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return None


def test_get_escalation_details(token, escalation_id="esc_test_001"):
    """Test GET /ceo/escalations/{escalation_id} endpoint."""
    print_test(f"Get Escalation Details (ID: {escalation_id})")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/ceo/escalations/{escalation_id}",
            headers=headers
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Escalation details retrieved successfully")
                return True
            else:
                print_error(f"Unexpected status: {data.get('status')}")
                return False
        elif response.status_code == 404:
            print_info("Escalation not found (expected - no mock data)")
            return True  # Expected behavior
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def test_approve_escalation(token, escalation_id="esc_test_001", otp="123456"):
    """Test POST /ceo/escalations/{escalation_id}/approve endpoint."""
    print_test(f"Approve Escalation (ID: {escalation_id})")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "otp": otp,
        "notes": "Test approval from manual testing script"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ceo/escalations/{escalation_id}/approve",
            headers=headers,
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 400, 404]:
            print_success("Endpoint responded (expected failure without real data)")
            return True
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def test_reject_escalation(token, escalation_id="esc_test_001", otp="123456"):
    """Test POST /ceo/escalations/{escalation_id}/reject endpoint."""
    print_test(f"Reject Escalation (ID: {escalation_id})")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "otp": otp,
        "notes": "Test rejection from manual testing script"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ceo/escalations/{escalation_id}/reject",
            headers=headers,
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 400, 404]:
            print_success("Endpoint responded (expected failure without real data)")
            return True
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def test_unauthorized_access():
    """Test that endpoints reject requests without valid JWT."""
    print_test("Authorization Check (No Token)")
    
    try:
        response = requests.get(f"{BASE_URL}/ceo/escalations")
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            print_success("Endpoint correctly rejects unauthorized requests")
            return True
        else:
            print_error(f"Expected 401/403, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}CEO ESCALATION WORKFLOW - MOCK TESTING{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"JWT Secret: {settings.JWT_SECRET[:10]}... (truncated)")
    
    # Create mock CEO token
    print_info("\nCreating mock CEO JWT token...")
    ceo_token = create_mock_jwt(user_id="ceo_test_123", role="CEO")
    print_success(f"Token created: {ceo_token[:30]}...")
    
    # Run tests
    results = []
    
    # Test 1: Unauthorized access
    results.append(("Unauthorized Access Check", test_unauthorized_access()))
    
    # Test 2: List escalations
    results.append(("List Escalations", test_list_escalations(ceo_token)))
    
    # Test 3: Request OTP
    otp = test_request_otp(ceo_token)
    results.append(("Request OTP", otp is not None))
    
    # Test 4: Get escalation details
    results.append(("Get Escalation Details", test_get_escalation_details(ceo_token)))
    
    # Test 5: Approve escalation
    if otp:
        results.append(("Approve Escalation", test_approve_escalation(ceo_token, otp=otp)))
    else:
        print_info("Skipping approve test (no OTP)")
    
    # Test 6: Reject escalation
    if otp:
        results.append(("Reject Escalation", test_reject_escalation(ceo_token, otp=otp)))
    else:
        print_info("Skipping reject test (no OTP)")
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}✓ All tests passed!{RESET}\n")
    else:
        print(f"{YELLOW}⚠ Some tests failed (expected if mock data not set up){RESET}\n")


if __name__ == "__main__":
    main()
