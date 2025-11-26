#!/usr/bin/env python3
"""
Test 1: CEO Registration with Meta Sandbox Number

Tests:
- Phone mapping (+15556337144 → +2348155563371)
- CEO registration flow
- OTP generation and delivery
- OTP verification
- JWT token generation
"""

import requests
import json
import time

# Configuration
API_BASE = "http://localhost:8000"
META_SANDBOX_PHONE = "+15556337144"  # Maps to +2348155563371
CEO_EMAIL = "abdurrazzaaq.jb@gmail.com"  # Changed from .test to .com
CEO_NAME = "Test CEO"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def print_step(step, text):
    print(f"\n{Colors.BOLD}Step {step}: {text}{Colors.RESET}")


def test_ceo_registration():
    """Test CEO registration with Meta sandbox number."""
    print_header("TEST 1: CEO REGISTRATION (META SANDBOX NUMBER)")
    
    # Step 1: Register CEO
    print_step(1, f"Register CEO with {META_SANDBOX_PHONE}")
    
    payload = {
        "name": CEO_NAME,
        "phone": META_SANDBOX_PHONE,
        "email": CEO_EMAIL
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/ceo/register",
            json=payload,
            timeout=10
        )
        
        print_info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            ceo_id = data.get('data', {}).get('ceo_id')
            dev_otp = data.get('data', {}).get('dev_otp')
            
            if ceo_id:
                print_success(f"CEO registered: {ceo_id}")
                print_info(f"Phone mapping: {META_SANDBOX_PHONE} → +2348155563371")
                
                if dev_otp:
                    print_info(f"Dev OTP: {dev_otp}")
                    
                    # Step 2: Verify OTP
                    print_step(2, "Verify CEO OTP")
                    
                    verify_payload = {
                        "user_id": ceo_id,
                        "otp": dev_otp
                    }
                    
                    verify_response = requests.post(
                        f"{API_BASE}/auth/verify-otp",
                        json=verify_payload,
                        timeout=10
                    )
                    
                    print_info(f"Verify Response Status: {verify_response.status_code}")
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        print_info(f"Response: {json.dumps(verify_data, indent=2)}")
                        
                        if verify_data.get('data', {}).get('valid'):
                            token = verify_data.get('data', {}).get('token')
                            print_success(f"CEO verified successfully!")
                            print_info(f"JWT Token: {token[:50]}...")
                            
                            # Step 3: Test authenticated endpoint
                            print_step(3, "Test authenticated CEO endpoint")
                            
                            headers = {"Authorization": f"Bearer {token}"}
                            profile_response = requests.get(
                                f"{API_BASE}/ceo/profile",
                                headers=headers,
                                timeout=10
                            )
                            
                            if profile_response.status_code == 200:
                                profile = profile_response.json()
                                print_success("CEO profile retrieved successfully!")
                                print_info(f"Profile: {json.dumps(profile, indent=2)}")
                            else:
                                print_error(f"Profile fetch failed: {profile_response.text}")
                        else:
                            print_error("OTP verification failed")
                    else:
                        print_error(f"OTP verification failed: {verify_response.text}")
                else:
                    print_error("No dev_otp in response (check ENVIRONMENT=dev)")
            else:
                print_error("No ceo_id in response")
        else:
            print_error(f"Registration failed: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the server running on port 8000?")
        print_info("Run: ./start_testing.sh")
    except Exception as e:
        print_error(f"Exception: {str(e)}")


def main():
    print(f"\n{Colors.BOLD}🧪 TrustGuard E2E Testing - CEO Registration{Colors.RESET}\n")
    
    # Test API health first
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code == 200:
            print_success(f"API is running: {health.json()}")
        else:
            print_error(f"API returned {health.status_code}")
            return
    except:
        print_error("API not reachable. Start server with: ./start_testing.sh")
        return
    
    # Run CEO registration test
    test_ceo_registration()
    
    # Summary
    print_header("TEST SUMMARY")
    print_info("✅ CEO registration test completed!")
    print_info("📱 Check server logs for phone mapping confirmation")
    print_info("\n💡 Next: Test WhatsApp/Instagram buyer flows")
    print()


if __name__ == "__main__":
    main()
