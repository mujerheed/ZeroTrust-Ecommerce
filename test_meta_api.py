#!/usr/bin/env python3
"""
Meta API Test Script
Tests WhatsApp and Instagram API connectivity with your credentials
"""

import os
import sys
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class MetaAPITester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def print_test(self, name: str):
        print(f"{Colors.BLUE}🧪 Testing:{Colors.END} {name}")
    
    def print_success(self, message: str):
        print(f"   {Colors.GREEN}✅ {message}{Colors.END}")
        self.tests_passed += 1
    
    def print_error(self, message: str):
        print(f"   {Colors.RED}❌ {message}{Colors.END}")
        self.tests_failed += 1
    
    def print_warning(self, message: str):
        print(f"   {Colors.YELLOW}⚠️  {message}{Colors.END}")
    
    def print_info(self, message: str):
        print(f"   {Colors.CYAN}ℹ️  {message}{Colors.END}")
    
    def test_whatsapp_connection(self) -> bool:
        """Test WhatsApp Business API connection"""
        self.print_test("WhatsApp Business API Connection")
        
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        
        if not phone_number_id or not access_token:
            self.print_warning("WhatsApp credentials not configured in .env")
            self.print_info("Add WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN to .env")
            return False
        
        try:
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Connected to WhatsApp Business API")
                self.print_info(f"Phone Number ID: {phone_number_id}")
                self.print_info(f"Display Name: {data.get('display_phone_number', 'N/A')}")
                self.print_info(f"Verified: {data.get('verified_name', 'N/A')}")
                self.print_info(f"Quality Rating: {data.get('quality_rating', 'N/A')}")
                return True
            elif response.status_code == 401:
                self.print_error("Invalid access token")
                self.print_info("Generate a new access token from Meta Business Suite")
                return False
            elif response.status_code == 403:
                self.print_error("Access forbidden - check token permissions")
                self.print_info("Ensure token has 'whatsapp_business_messaging' permission")
                return False
            else:
                self.print_error(f"API returned status {response.status_code}")
                self.print_info(f"Response: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            self.print_error("Request timed out")
            self.print_info("Check your internet connection")
            return False
        except requests.exceptions.ConnectionError:
            self.print_error("Connection failed")
            self.print_info("Check your internet connection")
            return False
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
            return False
    
    def test_instagram_connection(self) -> bool:
        """Test Instagram Messaging API connection"""
        self.print_test("Instagram Messaging API Connection")
        
        account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
        access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        
        if not account_id or not access_token:
            self.print_warning("Instagram credentials not configured in .env")
            self.print_info("Add INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN to .env")
            return False
        
        try:
            url = f"https://graph.facebook.com/v18.0/{account_id}"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"fields": "id,username,name,profile_picture_url"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Connected to Instagram Messaging API")
                self.print_info(f"Account ID: {account_id}")
                self.print_info(f"Username: @{data.get('username', 'N/A')}")
                self.print_info(f"Name: {data.get('name', 'N/A')}")
                return True
            elif response.status_code == 401:
                self.print_error("Invalid access token")
                self.print_info("Generate a new access token from Meta Business Suite")
                return False
            elif response.status_code == 403:
                self.print_error("Access forbidden - check token permissions")
                self.print_info("Ensure token has 'instagram_basic' and 'instagram_manage_messages' permissions")
                return False
            else:
                self.print_error(f"API returned status {response.status_code}")
                self.print_info(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
            return False
    
    def test_webhook_endpoints(self) -> bool:
        """Test local webhook endpoints"""
        self.print_test("Local Webhook Endpoints")
        
        backend_url = "http://localhost:8000"
        
        try:
            # Test health endpoint
            response = requests.get(f"{backend_url}/", timeout=5)
            
            if response.status_code == 200:
                self.print_success("Backend server is running")
                self.print_info(f"URL: {backend_url}")
            else:
                self.print_warning("Backend server responded but may have issues")
            
            # Check webhook routes exist
            self.print_info("Webhook endpoints should be at:")
            self.print_info(f"  WhatsApp: {backend_url}/integrations/webhook/whatsapp")
            self.print_info(f"  Instagram: {backend_url}/integrations/webhook/instagram")
            
            return True
            
        except requests.exceptions.ConnectionError:
            self.print_error("Backend server not running")
            self.print_info("Start backend: cd backend && uvicorn app:app --reload")
            return False
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
            return False
    
    def test_environment_config(self) -> bool:
        """Test environment configuration"""
        self.print_test("Environment Configuration")
        
        required_vars = {
            "Meta App": ["META_APP_ID", "META_APP_SECRET"],
            "WhatsApp": ["WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN"],
            "Instagram": ["INSTAGRAM_ACCOUNT_ID", "INSTAGRAM_ACCESS_TOKEN"],
            "Webhook": ["META_WEBHOOK_VERIFY_TOKEN"]
        }
        
        all_configured = True
        
        for category, vars_list in required_vars.items():
            missing = [var for var in vars_list if not os.getenv(var)]
            
            if missing:
                self.print_warning(f"{category}: {', '.join(missing)} not set")
                all_configured = False
            else:
                self.print_success(f"{category}: All credentials configured")
        
        if not all_configured:
            self.print_info("Run ./setup_meta_api.sh to configure missing credentials")
        
        return all_configured
    
    def print_summary(self):
        """Print test summary"""
        total_tests = self.tests_passed + self.tests_failed
        
        self.print_header("TEST SUMMARY")
        
        print(f"{Colors.GREEN}✅ Passed:{Colors.END} {self.tests_passed}")
        print(f"{Colors.RED}❌ Failed:{Colors.END} {self.tests_failed}")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.END}")
            print(f"{Colors.GREEN}Meta API is ready for production! 🚀{Colors.END}\n")
        else:
            print(f"\n{Colors.YELLOW}Some tests failed. Check the output above for details.{Colors.END}\n")
        
        print(f"\n{Colors.CYAN}{'='*70}{Colors.END}\n")
        
        # Print next steps
        print(f"{Colors.BOLD}NEXT STEPS:{Colors.END}\n")
        
        if self.tests_failed > 0:
            print("1. 🔧 Fix configuration issues above")
            print("2. 📖 Review META_API_SETUP_GUIDE.md")
            print("3. 🔄 Run this test script again: python3 test_meta_api.py")
        else:
            print("1. 🌐 Start ngrok tunnel:")
            print("   ngrok http 8000")
            print()
            print("2. 📝 Update webhook URLs in Meta Dashboard:")
            print("   WhatsApp: https://YOUR_NGROK_URL/integrations/webhook/whatsapp")
            print("   Instagram: https://YOUR_NGROK_URL/integrations/webhook/instagram")
            print()
            print("3. 📱 Send test message:")
            print("   WhatsApp: Send message to your business number")
            print("   Instagram: DM your business account")
            print()
            print("4. 📊 Monitor logs:")
            print("   tail -f /tmp/backend.log | grep WEBHOOK")
        print()

def main():
    tester = MetaAPITester()
    
    tester.print_header("TrustGuard Meta API Test Suite")
    
    # Run tests
    tester.test_environment_config()
    print()
    
    tester.test_webhook_endpoints()
    print()
    
    tester.test_whatsapp_connection()
    print()
    
    tester.test_instagram_connection()
    print()
    
    # Summary
    tester.print_summary()

if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print(f"{Colors.RED}❌ 'requests' library not installed{Colors.END}")
        print(f"{Colors.CYAN}Install: pip install requests{Colors.END}")
        sys.exit(1)
    
    # Check if python-dotenv is installed
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(f"{Colors.RED}❌ 'python-dotenv' library not installed{Colors.END}")
        print(f"{Colors.CYAN}Install: pip install python-dotenv{Colors.END}")
        sys.exit(1)
    
    main()
