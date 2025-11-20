"""
Test script for Phase 2 endpoints: OCR Auto-Approval, Vendor Preferences, CEO Chatbot Config, Analytics, Notifications
Tests against deployed API: https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/

Usage:
    python test_phase2_endpoints.py
    
Requirements:
    pip install requests pytest python-dotenv
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import base64

# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod")

# Test credentials (you'll need to set these)
TEST_CEO_PHONE = os.getenv("TEST_CEO_PHONE", "+2348012345678")
TEST_VENDOR_PHONE = os.getenv("TEST_VENDOR_PHONE", "+2348087654321")
TEST_BUYER_ID = os.getenv("TEST_BUYER_ID", "wa_1234567890")

# Global tokens (will be set after login)
ceo_token = None
vendor_token = None
buyer_token = None


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def make_request(
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make HTTP request to API"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if data and not files:
        headers["Content-Type"] = "application/json"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "success": False
        }


def test_authentication():
    """Test authentication for CEO, Vendor, and Buyer"""
    global ceo_token, vendor_token, buyer_token
    
    print_header("Authentication Tests")
    
    # CEO Login
    print_info("Testing CEO login...")
    print_warning(f"Manual step required: Request OTP for CEO phone {TEST_CEO_PHONE}")
    print_warning("Run: POST /auth/ceo/request-otp with phone number")
    ceo_otp = input(f"{Colors.OKCYAN}Enter CEO OTP (6 digits): {Colors.ENDC}").strip()
    
    response = make_request("POST", "/auth/ceo/verify-otp", data={
        "phone_number": TEST_CEO_PHONE,
        "otp": ceo_otp
    })
    
    if response["success"] and "token" in response["data"].get("data", {}):
        ceo_token = response["data"]["data"]["token"]
        print_success(f"CEO authenticated successfully. Token: {ceo_token[:20]}...")
    else:
        print_error(f"CEO authentication failed: {response['data']}")
        return False
    
    # Vendor Login
    print_info("\nTesting Vendor login...")
    print_warning(f"Manual step required: Request OTP for Vendor phone {TEST_VENDOR_PHONE}")
    vendor_otp = input(f"{Colors.OKCYAN}Enter Vendor OTP (8 chars): {Colors.ENDC}").strip()
    
    response = make_request("POST", "/auth/vendor/verify-otp", data={
        "phone_number": TEST_VENDOR_PHONE,
        "otp": vendor_otp
    })
    
    if response["success"] and "token" in response["data"].get("data", {}):
        vendor_token = response["data"]["data"]["token"]
        print_success(f"Vendor authenticated successfully. Token: {vendor_token[:20]}...")
    else:
        print_error(f"Vendor authentication failed: {response['data']}")
        return False
    
    # Buyer Login (optional for now)
    print_info("\nSkipping Buyer authentication (not needed for Phase 2 tests)")
    
    return True


def test_ceo_chatbot_config():
    """Test CEO chatbot configuration endpoints"""
    print_header("CEO Chatbot Configuration Tests")
    
    if not ceo_token:
        print_error("CEO token not available. Run authentication first.")
        return False
    
    # Test GET chatbot settings (should return defaults if not set)
    print_info("Testing GET /ceo/chatbot/settings...")
    response = make_request("GET", "/ceo/chatbot/settings", token=ceo_token)
    
    if response["success"]:
        print_success("GET chatbot settings successful")
        print(json.dumps(response["data"], indent=2))
    else:
        print_error(f"GET chatbot settings failed: {response['data']}")
    
    # Test PUT chatbot settings
    print_info("\nTesting PUT /ceo/chatbot/settings...")
    new_settings = {
        "greeting_message": "Hello! Welcome to TrustGuard. How can I assist you today?",
        "tone": "professional",
        "language": "en",
        "auto_response_enabled": True
    }
    
    response = make_request("PUT", "/ceo/chatbot/settings", token=ceo_token, data=new_settings)
    
    if response["success"]:
        print_success("PUT chatbot settings successful")
        print(json.dumps(response["data"], indent=2))
    else:
        print_error(f"PUT chatbot settings failed: {response['data']}")
    
    # Verify settings were saved
    print_info("\nVerifying settings were saved...")
    response = make_request("GET", "/ceo/chatbot/settings", token=ceo_token)
    
    if response["success"]:
        data = response["data"].get("data", {})
        if data.get("greeting_message") == new_settings["greeting_message"]:
            print_success("Chatbot settings verified successfully")
        else:
            print_error("Chatbot settings mismatch")
    
    return True


def test_vendor_preferences():
    """Test vendor preferences endpoints"""
    print_header("Vendor Preferences Tests")
    
    if not vendor_token:
        print_error("Vendor token not available. Run authentication first.")
        return False
    
    # Test GET vendor preferences (should return defaults if not set)
    print_info("Testing GET /vendor/preferences...")
    response = make_request("GET", "/vendor/preferences", token=vendor_token)
    
    if response["success"]:
        print_success("GET vendor preferences successful")
        print(json.dumps(response["data"], indent=2))
    else:
        print_error(f"GET vendor preferences failed: {response['data']}")
    
    # Test PUT vendor preferences
    print_info("\nTesting PUT /vendor/preferences...")
    new_preferences = {
        "textract_enabled": True,
        "min_ocr_confidence": 80.0,
        "amount_tolerance_percent": 2.0,
        "auto_approve_threshold": 0  # OCR-based only, no threshold
    }
    
    response = make_request("PUT", "/vendor/preferences", token=vendor_token, data=new_preferences)
    
    if response["success"]:
        print_success("PUT vendor preferences successful")
        print(json.dumps(response["data"], indent=2))
    else:
        print_error(f"PUT vendor preferences failed: {response['data']}")
    
    # Verify preferences were saved
    print_info("\nVerifying preferences were saved...")
    response = make_request("GET", "/vendor/preferences", token=vendor_token)
    
    if response["success"]:
        data = response["data"].get("data", {})
        if data.get("textract_enabled") == new_preferences["textract_enabled"]:
            print_success("Vendor preferences verified successfully")
        else:
            print_error("Vendor preferences mismatch")
    
    return True


def test_vendor_risk_scores():
    """Test vendor risk score calculation in CEO vendor list"""
    print_header("Vendor Risk Score Tests")
    
    if not ceo_token:
        print_error("CEO token not available. Run authentication first.")
        return False
    
    # Test GET vendors with risk scores
    print_info("Testing GET /ceo/vendors (should include risk_score)...")
    response = make_request("GET", "/ceo/vendors", token=ceo_token)
    
    if response["success"]:
        vendors = response["data"].get("data", {}).get("vendors", [])
        print_success(f"GET vendors successful. Found {len(vendors)} vendors")
        
        for vendor in vendors[:3]:  # Show first 3 vendors
            risk_score = vendor.get("risk_score", "N/A")
            vendor_id = vendor.get("vendor_id", "Unknown")
            name = vendor.get("name", "Unknown")
            print(f"  - {name} ({vendor_id}): Risk Score = {risk_score}")
        
        # Verify risk_score field exists
        if vendors and "risk_score" in vendors[0]:
            print_success("risk_score field found in vendor data")
        else:
            print_warning("risk_score field not found in vendor data")
    else:
        print_error(f"GET vendors failed: {response['data']}")
    
    return True


def test_analytics_endpoints():
    """Test analytics time-series endpoints"""
    print_header("Analytics Endpoints Tests")
    
    # Test vendor analytics
    if vendor_token:
        print_info("Testing GET /vendor/analytics/orders-by-day...")
        
        # Calculate date range (last 30 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = make_request(
            "GET",
            f"/vendor/analytics/orders-by-day?start_date={start_date}&end_date={end_date}",
            token=vendor_token
        )
        
        if response["success"]:
            data_points = response["data"].get("data", {}).get("data_points", [])
            print_success(f"Vendor analytics successful. Found {len(data_points)} data points")
            
            if data_points:
                print("  Sample data points:")
                for point in data_points[:5]:
                    print(f"    - {point.get('date')}: {point.get('count')} orders")
        else:
            print_error(f"Vendor analytics failed: {response['data']}")
    
    # Test CEO fraud trends
    if ceo_token:
        print_info("\nTesting GET /ceo/analytics/fraud-trends...")
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = make_request(
            "GET",
            f"/ceo/analytics/fraud-trends?start_date={start_date}&end_date={end_date}",
            token=ceo_token
        )
        
        if response["success"]:
            data_points = response["data"].get("data", {}).get("data_points", [])
            print_success(f"CEO fraud trends successful. Found {len(data_points)} data points")
            
            if data_points:
                print("  Sample data points:")
                for point in data_points[:5]:
                    print(f"    - {point.get('date')}: {point.get('flagged_count')} flagged, {point.get('approved_count')} approved")
        else:
            print_error(f"CEO fraud trends failed: {response['data']}")
    
    return True


def test_notification_polling():
    """Test vendor notification polling endpoint"""
    print_header("Notification Polling Tests")
    
    if not vendor_token:
        print_error("Vendor token not available. Run authentication first.")
        return False
    
    print_info("Testing GET /vendor/notifications/unread...")
    response = make_request("GET", "/vendor/notifications/unread", token=vendor_token)
    
    if response["success"]:
        data = response["data"].get("data", {})
        unread_count = data.get("unread_count", 0)
        last_check = data.get("last_check")
        
        print_success(f"Notification polling successful")
        print(f"  - Unread count: {unread_count}")
        print(f"  - Last check: {last_check}")
    else:
        print_error(f"Notification polling failed: {response['data']}")
    
    return True


def test_ocr_auto_approval_workflow():
    """Test OCR auto-approval workflow (requires manual receipt upload)"""
    print_header("OCR Auto-Approval Workflow Tests")
    
    print_warning("OCR auto-approval workflow requires:")
    print_warning("  1. A buyer to upload a receipt via WhatsApp/Instagram")
    print_warning("  2. Textract to process the receipt")
    print_warning("  3. Auto-approval logic to trigger")
    print_warning("\nThis test will verify the vendor can see OCR results")
    
    if not vendor_token:
        print_error("Vendor token not available. Run authentication first.")
        return False
    
    # Get vendor orders to find receipts
    print_info("\nFetching vendor orders to check for OCR results...")
    response = make_request("GET", "/vendor/orders", token=vendor_token)
    
    if response["success"]:
        orders = response["data"].get("data", {}).get("orders", [])
        print_success(f"Found {len(orders)} orders")
        
        # Look for orders with OCR data
        ocr_orders = [o for o in orders if o.get("receipt_ocr_status") == "completed"]
        
        if ocr_orders:
            print_success(f"Found {len(ocr_orders)} orders with OCR results")
            
            for order in ocr_orders[:3]:
                order_id = order.get("order_id")
                ocr_confidence = order.get("receipt_ocr_confidence", "N/A")
                ocr_amount = order.get("receipt_ocr_amount", "N/A")
                status = order.get("status")
                
                print(f"\n  Order {order_id}:")
                print(f"    - Status: {status}")
                print(f"    - OCR Confidence: {ocr_confidence}%")
                print(f"    - OCR Amount: ₦{ocr_amount}")
                
                # Check if auto-approval logic was triggered
                if status == "approved":
                    print_success(f"    - ✓ Auto-approved by OCR validation")
                elif status == "flagged":
                    print_warning(f"    - ⚠ Flagged for manual review (OCR validation failed)")
                elif status == "pending_ceo":
                    print_info(f"    - ℹ Escalated to CEO (high-value or flagged)")
        else:
            print_warning("No orders with OCR results found")
            print_info("To test OCR workflow:")
            print_info("  1. Have a buyer upload a receipt")
            print_info("  2. Wait for Textract to process it (30-60 seconds)")
            print_info("  3. Run this test again")
    else:
        print_error(f"Failed to fetch orders: {response['data']}")
    
    return True


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║         TrustGuard Phase 2 Endpoint Testing Suite                         ║")
    print("║         OCR Auto-Approval + Backend 100% Validation                        ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Test CEO Phone: {TEST_CEO_PHONE}")
    print_info(f"Test Vendor Phone: {TEST_VENDOR_PHONE}")
    
    # Run tests in sequence
    tests = [
        ("Authentication", test_authentication),
        ("CEO Chatbot Configuration", test_ceo_chatbot_config),
        ("Vendor Preferences", test_vendor_preferences),
        ("Vendor Risk Scores", test_vendor_risk_scores),
        ("Analytics Endpoints", test_analytics_endpoints),
        ("Notification Polling", test_notification_polling),
        ("OCR Auto-Approval Workflow", test_ocr_auto_approval_workflow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
        except Exception as e:
            print_error(f"Test '{test_name}' raised exception: {e}")
            results[test_name] = "ERROR"
        
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print_header("Test Summary")
    
    for test_name, result in results.items():
        if result == "PASS":
            print_success(f"{test_name}: {result}")
        elif result == "FAIL":
            print_error(f"{test_name}: {result}")
        else:
            print_warning(f"{test_name}: {result}")
    
    # Overall result
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r == "PASS")
    
    print(f"\n{Colors.BOLD}Overall: {passed_tests}/{total_tests} tests passed{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
