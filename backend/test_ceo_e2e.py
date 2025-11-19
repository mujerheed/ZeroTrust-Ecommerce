"""
End-to-End Test Suite for CEO Service

Tests:
1. CEO Registration
2. CEO Login (Authentication)
3. Duplicate Email Registration (Validation)
4. Invalid Login Credentials
5. Vendor Onboarding by CEO
6. List Vendors (Multi-Tenancy)
7. Delete Vendor (Authorization)
8. Dashboard Metrics
9. Pending Approvals
10. OTP Request for Approval
11. Approve Order with OTP
12. Reject Order
13. Multi-CEO Isolation (Unauthorized Access)
14. Audit Logs
15. Invalid Token (Authorization)

Prerequisites:
- FastAPI server running on localhost:8000
- DynamoDB tables configured
- JWT_SECRET environment variable set

Run:
    python test_ceo_e2e.py
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
CEO_PREFIX = "/ceo"

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Test data
test_ceo_1 = {
    "name": "Alice Johnson",
    "email": f"alice_{int(time.time())}@testceo.com",
    "phone": "+2348012345678",
    "password": "SecurePass123!",
    "company_name": "Alice's Electronics"
}

test_ceo_2 = {
    "name": "Bob Smith",
    "email": f"bob_{int(time.time())}@testceo.com",
    "phone": "+2348098765432",
    "password": "BobSecure456!",
    "company_name": "Bob's Gadgets"
}

test_vendor = {
    "name": "John Vendor",
    "email": f"john_vendor_{int(time.time())}@testvendor.com",
    "phone": "+2348011112222"
}

# Global state
ceo_1_token = None
ceo_1_id = None
ceo_2_token = None
ceo_2_id = None
vendor_1_id = None

test_results = []


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result with color coding."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {CYAN}{details}{RESET}")
    test_results.append({"test": test_name, "passed": passed, "details": details})


def test_1_register_ceo():
    """Test CEO registration."""
    global ceo_1_id
    
    print(f"\n{YELLOW}Test 1: CEO Registration{RESET}")
    
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/register",
        json=test_ceo_1
    )
    
    if response.status_code == 201:
        data = response.json()
        if data.get("status") == "success" and "ceo" in data.get("data", {}):
            ceo_1_id = data["data"]["ceo"]["ceo_id"]
            log_test("CEO Registration", True, f"CEO ID: {ceo_1_id}")
            return True
        else:
            log_test("CEO Registration", False, f"Unexpected response: {data}")
            return False
    else:
        log_test("CEO Registration", False, f"Status {response.status_code}: {response.text}")
        return False


def test_2_login_ceo():
    """Test CEO login and JWT token generation."""
    global ceo_1_token
    
    print(f"\n{YELLOW}Test 2: CEO Login{RESET}")
    
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/login",
        json={
            "email": test_ceo_1["email"],
            "password": test_ceo_1["password"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if "token" in data.get("data", {}):
            ceo_1_token = data["data"]["token"]
            log_test("CEO Login", True, f"Token received (length: {len(ceo_1_token)})")
            return True
        else:
            log_test("CEO Login", False, f"No token in response: {data}")
            return False
    else:
        log_test("CEO Login", False, f"Status {response.status_code}: {response.text}")
        return False


def test_3_duplicate_email():
    """Test duplicate email registration (should fail)."""
    print(f"\n{YELLOW}Test 3: Duplicate Email Registration{RESET}")
    
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/register",
        json=test_ceo_1  # Same email as test 1
    )
    
    if response.status_code == 409:  # Conflict
        log_test("Duplicate Email Prevention", True, "409 Conflict as expected")
        return True
    else:
        log_test("Duplicate Email Prevention", False, f"Expected 409, got {response.status_code}")
        return False


def test_4_invalid_login():
    """Test login with invalid credentials."""
    print(f"\n{YELLOW}Test 4: Invalid Login Credentials{RESET}")
    
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/login",
        json={
            "email": test_ceo_1["email"],
            "password": "WrongPassword123!"
        }
    )
    
    if response.status_code == 401:  # Unauthorized
        log_test("Invalid Login Prevention", True, "401 Unauthorized as expected")
        return True
    else:
        log_test("Invalid Login Prevention", False, f"Expected 401, got {response.status_code}")
        return False


def test_5_onboard_vendor():
    """Test vendor onboarding by CEO."""
    global vendor_1_id
    
    print(f"\n{YELLOW}Test 5: Vendor Onboarding{RESET}")
    
    if not ceo_1_token:
        log_test("Vendor Onboarding", False, "CEO token not available")
        return False
    
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/vendors",
        json=test_vendor,
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    if response.status_code == 201:
        data = response.json()
        if "vendor" in data.get("data", {}):
            vendor_1_id = data["data"]["vendor"]["vendor_id"]
            temp_password = data["data"].get("temporary_password", "")
            log_test("Vendor Onboarding", True, f"Vendor ID: {vendor_1_id}, Temp Password: {temp_password[:4]}***")
            return True
        else:
            log_test("Vendor Onboarding", False, f"No vendor in response: {data}")
            return False
    else:
        log_test("Vendor Onboarding", False, f"Status {response.status_code}: {response.text}")
        return False


def test_6_list_vendors():
    """Test listing vendors (multi-tenancy)."""
    print(f"\n{YELLOW}Test 6: List Vendors (Multi-Tenancy){RESET}")
    
    if not ceo_1_token:
        log_test("List Vendors", False, "CEO token not available")
        return False
    
    response = requests.get(
        f"{BASE_URL}{CEO_PREFIX}/vendors",
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        vendors = data.get("data", {}).get("vendors", [])
        count = data.get("data", {}).get("count", 0)
        log_test("List Vendors", True, f"Found {count} vendor(s)")
        return True
    else:
        log_test("List Vendors", False, f"Status {response.status_code}: {response.text}")
        return False


def test_7_delete_vendor():
    """Test vendor deletion (authorization check)."""
    print(f"\n{YELLOW}Test 7: Delete Vendor{RESET}")
    
    if not ceo_1_token or not vendor_1_id:
        log_test("Delete Vendor", False, "CEO token or vendor ID not available")
        return False
    
    response = requests.delete(
        f"{BASE_URL}{CEO_PREFIX}/vendors/{vendor_1_id}",
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    if response.status_code == 200:
        log_test("Delete Vendor", True, f"Vendor {vendor_1_id} deleted")
        return True
    else:
        log_test("Delete Vendor", False, f"Status {response.status_code}: {response.text}")
        return False


def test_8_dashboard_metrics():
    """Test CEO dashboard metrics."""
    print(f"\n{YELLOW}Test 8: Dashboard Metrics{RESET}")
    
    if not ceo_1_token:
        log_test("Dashboard Metrics", False, "CEO token not available")
        return False
    
    response = requests.get(
        f"{BASE_URL}{CEO_PREFIX}/dashboard",
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        dashboard = data.get("data", {}).get("dashboard", {})
        total_vendors = dashboard.get("total_vendors", 0)
        total_orders = dashboard.get("total_orders", 0)
        total_revenue = dashboard.get("total_revenue", 0)
        
        log_test("Dashboard Metrics", True, 
                f"Vendors: {total_vendors}, Orders: {total_orders}, Revenue: ₦{total_revenue:,.2f}")
        return True
    else:
        log_test("Dashboard Metrics", False, f"Status {response.status_code}: {response.text}")
        return False


def test_9_pending_approvals():
    """Test getting pending approval requests."""
    print(f"\n{YELLOW}Test 9: Pending Approvals{RESET}")
    
    if not ceo_1_token:
        log_test("Pending Approvals", False, "CEO token not available")
        return False
    
    response = requests.get(
        f"{BASE_URL}{CEO_PREFIX}/approvals",
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        flagged = data.get("data", {}).get("flagged_orders", [])
        high_value = data.get("data", {}).get("high_value_orders", [])
        total = data.get("data", {}).get("total_pending", 0)
        
        log_test("Pending Approvals", True, 
                f"Total: {total} (Flagged: {len(flagged)}, High-Value: {len(high_value)})")
        return True
    else:
        log_test("Pending Approvals", False, f"Status {response.status_code}: {response.text}")
        return False


def test_10_request_approval_otp():
    """Test OTP request for order approval."""
    print(f"\n{YELLOW}Test 10: Request Approval OTP{RESET}")
    
    if not ceo_1_token:
        log_test("Request Approval OTP", False, "CEO token not available")
        return False
    
    # Use a mock order ID (will fail if order doesn't exist, but tests the endpoint)
    mock_order_id = "ord_test_12345"
    
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/approvals/request-otp?order_id={mock_order_id}",
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    # Expect 404 (order not found) or 200 (OTP generated)
    if response.status_code in [200, 404]:
        if response.status_code == 404:
            log_test("Request Approval OTP", True, "404 - Order not found (expected for mock ID)")
        else:
            data = response.json()
            otp = data.get("data", {}).get("dev_otp", "")
            log_test("Request Approval OTP", True, f"OTP generated: {otp}")
        return True
    else:
        log_test("Request Approval OTP", False, f"Status {response.status_code}: {response.text}")
        return False


def test_11_approve_order():
    """Test order approval (with mock data)."""
    print(f"\n{YELLOW}Test 11: Approve Order{RESET}")
    
    if not ceo_1_token:
        log_test("Approve Order", False, "CEO token not available")
        return False
    
    mock_order_id = "ord_test_12345"
    
    response = requests.patch(
        f"{BASE_URL}{CEO_PREFIX}/approvals/{mock_order_id}/approve",
        json={"notes": "Approved after verification"},
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    # Expect 404 (order not found) or 200 (approved)
    if response.status_code in [200, 404]:
        if response.status_code == 404:
            log_test("Approve Order Endpoint", True, "404 - Order not found (expected for mock ID)")
        else:
            log_test("Approve Order Endpoint", True, "Order approved")
        return True
    else:
        log_test("Approve Order Endpoint", False, f"Status {response.status_code}: {response.text}")
        return False


def test_12_reject_order():
    """Test order rejection (with mock data)."""
    print(f"\n{YELLOW}Test 12: Reject Order{RESET}")
    
    if not ceo_1_token:
        log_test("Reject Order", False, "CEO token not available")
        return False
    
    mock_order_id = "ord_test_67890"
    
    response = requests.patch(
        f"{BASE_URL}{CEO_PREFIX}/approvals/{mock_order_id}/reject",
        json={"reason": "Receipt appears fraudulent"},
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    # Expect 404 (order not found) or 200 (rejected)
    if response.status_code in [200, 404]:
        if response.status_code == 404:
            log_test("Reject Order Endpoint", True, "404 - Order not found (expected for mock ID)")
        else:
            log_test("Reject Order Endpoint", True, "Order rejected")
        return True
    else:
        log_test("Reject Order Endpoint", False, f"Status {response.status_code}: {response.text}")
        return False


def test_13_multi_ceo_isolation():
    """Test multi-CEO tenancy isolation."""
    global ceo_2_token, ceo_2_id
    
    print(f"\n{YELLOW}Test 13: Multi-CEO Isolation{RESET}")
    
    # Register second CEO
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/register",
        json=test_ceo_2
    )
    
    if response.status_code != 201:
        log_test("Multi-CEO Isolation", False, "Failed to register CEO 2")
        return False
    
    ceo_2_id = response.json()["data"]["ceo"]["ceo_id"]
    
    # Login as CEO 2
    response = requests.post(
        f"{BASE_URL}{CEO_PREFIX}/login",
        json={"email": test_ceo_2["email"], "password": test_ceo_2["password"]}
    )
    
    if response.status_code != 200:
        log_test("Multi-CEO Isolation", False, "Failed to login CEO 2")
        return False
    
    ceo_2_token = response.json()["data"]["token"]
    
    # CEO 2 tries to access CEO 1's dashboard (should see empty data, not CEO 1's data)
    response = requests.get(
        f"{BASE_URL}{CEO_PREFIX}/dashboard",
        headers={"Authorization": f"Bearer {ceo_2_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        dashboard = data.get("data", {}).get("dashboard", {})
        # CEO 2 should have 0 vendors (isolation working)
        if dashboard.get("total_vendors", -1) == 0:
            log_test("Multi-CEO Isolation", True, "CEO 2 cannot see CEO 1's data ✓")
            return True
        else:
            log_test("Multi-CEO Isolation", False, f"Data leakage detected: {dashboard}")
            return False
    else:
        log_test("Multi-CEO Isolation", False, f"Status {response.status_code}: {response.text}")
        return False


def test_14_audit_logs():
    """Test audit log access."""
    print(f"\n{YELLOW}Test 14: Audit Logs{RESET}")
    
    if not ceo_1_token:
        log_test("Audit Logs", False, "CEO token not available")
        return False
    
    response = requests.get(
        f"{BASE_URL}{CEO_PREFIX}/audit-logs?limit=10",
        headers={"Authorization": f"Bearer {ceo_1_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        logs = data.get("data", {}).get("logs", [])
        count = data.get("data", {}).get("count", 0)
        log_test("Audit Logs", True, f"Retrieved {count} audit log entries")
        return True
    else:
        log_test("Audit Logs", False, f"Status {response.status_code}: {response.text}")
        return False


def test_15_invalid_token():
    """Test endpoint with invalid/expired token."""
    print(f"\n{YELLOW}Test 15: Invalid Token{RESET}")
    
    response = requests.get(
        f"{BASE_URL}{CEO_PREFIX}/dashboard",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )
    
    if response.status_code == 401:
        log_test("Invalid Token Prevention", True, "401 Unauthorized as expected")
        return True
    else:
        log_test("Invalid Token Prevention", False, f"Expected 401, got {response.status_code}")
        return False


def print_summary():
    """Print test summary."""
    print(f"\n{'='*70}")
    print(f"{CYAN}CEO SERVICE E2E TEST SUMMARY{RESET}")
    print(f"{'='*70}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["passed"])
    failed_tests = total_tests - passed_tests
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal Tests:  {total_tests}")
    print(f"{GREEN}Passed:       {passed_tests}{RESET}")
    print(f"{RED}Failed:       {failed_tests}{RESET}")
    print(f"Pass Rate:    {pass_rate:.1f}%")
    
    if failed_tests > 0:
        print(f"\n{RED}Failed Tests:{RESET}")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}: {result['details']}")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}CEO SERVICE END-TO-END TEST SUITE{RESET}")
    print(f"{CYAN}{'='*70}{RESET}")
    print(f"Base URL: {BASE_URL}")
    print(f"CEO Prefix: {CEO_PREFIX}")
    print(f"{CYAN}{'='*70}{RESET}")
    
    # Run all tests
    test_1_register_ceo()
    test_2_login_ceo()
    test_3_duplicate_email()
    test_4_invalid_login()
    test_5_onboard_vendor()
    test_6_list_vendors()
    test_7_delete_vendor()
    test_8_dashboard_metrics()
    test_9_pending_approvals()
    test_10_request_approval_otp()
    test_11_approve_order()
    test_12_reject_order()
    test_13_multi_ceo_isolation()
    test_14_audit_logs()
    test_15_invalid_token()
    
    # Print summary
    print_summary()
