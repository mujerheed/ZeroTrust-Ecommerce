"""
Simple authentication test to verify OTP flow works
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod")
TEST_CEO_PHONE = os.getenv("TEST_CEO_PHONE", "+2348133336318")
TEST_VENDOR_PHONE = os.getenv("TEST_VENDOR_PHONE", "+2348133336318")

def print_header(text):
    print(f"\n{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_info(text):
    print(f"ℹ {text}")

def test_ceo_request_otp():
    """Test CEO OTP request"""
    print_header("Testing CEO OTP Request (via /ceo/login)")
    
    print_info(f"Requesting OTP for CEO: {TEST_CEO_PHONE}")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/ceo/login",
        json={"contact": TEST_CEO_PHONE},  # CEO uses 'contact' field
        timeout=30
    )
    
    print_info(f"Status Code: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code == 200:
        print_success("OTP request successful!")
        # Extract ceo_id from response (it's the key in the data dict)
        data = response.json().get("data", {})
        # The response has ceo_id as a key, get the first key
        ceo_id = list(data.keys())[0] if data else None
        if ceo_id and ceo_id != "otp_format":
            print_info(f"CEO ID: {ceo_id}")
            return ceo_id
        return True
    else:
        print_error(f"OTP request failed: {response.text}")
        return None

def test_vendor_request_otp():
    """Test Vendor OTP request"""
    print_header("Testing Vendor OTP Request (via /vendor/login)")
    
    print_info(f"Requesting OTP for Vendor: {TEST_VENDOR_PHONE}")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/vendor/login",
        json={"phone": TEST_VENDOR_PHONE},  # Vendor uses 'phone' field
        timeout=30
    )
    
    print_info(f"Status Code: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code == 200:
        print_success("OTP request successful!")
        # Extract vendor_id from response
        data = response.json().get("data", {})
        vendor_id = list(data.keys())[0] if data else None
        if vendor_id and vendor_id != "otp_format":
            print_info(f"Vendor ID: {vendor_id}")
            return vendor_id
        return True
    else:
        print_error(f"OTP request failed: {response.text}")
        return None

def test_ceo_verify_otp(ceo_id):
    """Test CEO OTP verification"""
    print_header("Testing CEO OTP Verification (via /verify-otp)")
    
    otp = input("Enter the CEO OTP you received (6 digits): ").strip()
    
    print_info(f"Verifying OTP for CEO ID: {ceo_id}")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={
            "user_id": ceo_id,
            "otp": otp
        },
        timeout=30
    )
    
    print_info(f"Status Code: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("token")
        if token:
            print_success(f"CEO authentication successful!")
            print_info(f"Token: {token[:30]}...")
            return token
        else:
            print_error("No token in response")
            return None
    else:
        print_error(f"OTP verification failed: {response.text}")
        return None

def test_vendor_verify_otp(vendor_id):
    """Test Vendor OTP verification"""
    print_header("Testing Vendor OTP Verification (via /verify-otp)")
    
    otp = input("Enter the Vendor OTP you received (8 characters): ").strip()
    
    print_info(f"Verifying OTP for Vendor ID: {vendor_id}")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/verify-otp",
        json={
            "user_id": vendor_id,
            "otp": otp
        },
        timeout=30
    )
    
    print_info(f"Status Code: {response.status_code}")
    print_info(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("token")
        if token:
            print_success(f"Vendor authentication successful!")
            print_info(f"Token: {token[:30]}...")
            return token
        else:
            print_error("No token in response")
            return None
    else:
        print_error(f"OTP verification failed: {response.text}")
        return None

def test_endpoint_with_token(endpoint, token, role):
    """Test accessing an endpoint with token"""
    print_header(f"Testing {role} Endpoint Access")
    
    print_info(f"Testing endpoint: {endpoint}")
    
    response = requests.get(
        f"{API_BASE_URL}{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    
    print_info(f"Status Code: {response.status_code}")
    print_info(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        print_success(f"{role} endpoint accessible!")
        return True
    else:
        print_error(f"Endpoint access failed: {response.status_code}")
        return False

def main():
    print("\n╔════════════════════════════════════════════════════════════════════════════╗")
    print("║           TrustGuard Simple Authentication Test                           ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"CEO Phone: {TEST_CEO_PHONE}")
    print_info(f"Vendor Phone: {TEST_VENDOR_PHONE}")
    
    # Test CEO flow
    print("\n" + "="*80)
    print("CEO Authentication Flow".center(80))
    print("="*80)
    
    ceo_id = test_ceo_request_otp()
    if ceo_id:
        ceo_token = test_ceo_verify_otp(ceo_id)
        if ceo_token:
            test_endpoint_with_token("/ceo/vendors", ceo_token, "CEO")
    
    # Test Vendor flow
    print("\n" + "="*80)
    print("Vendor Authentication Flow".center(80))
    print("="*80)
    
    vendor_id = test_vendor_request_otp()
    if vendor_id:
        vendor_token = test_vendor_verify_otp(vendor_id)
        if vendor_token:
            test_endpoint_with_token("/vendor/orders", vendor_token, "Vendor")

if __name__ == "__main__":
    main()
