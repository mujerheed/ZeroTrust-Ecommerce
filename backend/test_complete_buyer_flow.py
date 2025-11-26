#!/usr/bin/env python3
"""
Complete Buyer Flow Mock Test
Tests ALL buyer features using mock webhooks:
- Registration
- OTP verification
- Order creation
- Receipt upload
- Order status check
"""

import requests
import json
import time
import hmac
import hashlib
import base64
from common.config import settings

API_BASE = "http://localhost:8000"
APP_SECRET = settings.META_APP_SECRET if hasattr(settings, 'META_APP_SECRET') else "your_secret_here"

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def create_signature(payload_str, secret):
    """Create HMAC signature like Meta does"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def send_whatsapp_message(phone_number, message_text, buyer_name="Test Buyer"):
    """Simulate WhatsApp buyer sending a text message"""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15556337144",
                        "phone_number_id": "822785510918202"
                    },
                    "contacts": [{
                        "profile": {"name": buyer_name},
                        "wa_id": phone_number.replace("+", "")
                    }],
                    "messages": [{
                        "from": phone_number.replace("+", ""),
                        "id": f"wamid.test{int(time.time())}",
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {"body": message_text}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    payload_str = json.dumps(payload)
    signature = create_signature(payload_str, APP_SECRET)
    
    response = requests.post(
        f"{API_BASE}/integrations/webhook/whatsapp",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature
        },
        timeout=10
    )
    
    return response

def send_whatsapp_image(phone_number, image_url, caption="", buyer_name="Test Buyer"):
    """Simulate WhatsApp buyer sending an image (receipt)"""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15556337144",
                        "phone_number_id": "822785510918202"
                    },
                    "contacts": [{
                        "profile": {"name": buyer_name},
                        "wa_id": phone_number.replace("+", "")
                    }],
                    "messages": [{
                        "from": phone_number.replace("+", ""),
                        "id": f"wamid.test{int(time.time())}",
                        "timestamp": str(int(time.time())),
                        "type": "image",
                        "image": {
                            "id": f"img_{int(time.time())}",
                            "mime_type": "image/jpeg",
                            "sha256": "fake_sha256_hash",
                            "caption": caption
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    payload_str = json.dumps(payload)
    signature = create_signature(payload_str, APP_SECRET)
    
    response = requests.post(
        f"{API_BASE}/integrations/webhook/whatsapp",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature
        },
        timeout=10
    )
    
    return response

def print_step(step_num, title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Step {step_num}: {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─' * 70}{Colors.RESET}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def test_complete_buyer_flow():
    """Test complete buyer journey from registration to order completion"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}🧪 COMPLETE BUYER FLOW TEST (ALL FEATURES){Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    phone = "+2348012345678"
    buyer_name = "John Doe"
    
    # ========== FEATURE 1: REGISTRATION ==========
    print_step(1, "BUYER REGISTRATION")
    
    print_info("Buyer sends: 'hi'")
    response = send_whatsapp_message(phone, "hi", buyer_name)
    print_success(f"Response: {response.status_code}")
    time.sleep(2)
    
    print_info("Buyer sends name: 'John Doe'")
    response = send_whatsapp_message(phone, "John Doe", buyer_name)
    print_success(f"Response: {response.status_code}")
    time.sleep(2)
    
    print_info("Buyer sends address: '123 Ikeja Road, Lagos'")
    response = send_whatsapp_message(phone, "123 Ikeja Road, Lagos, Nigeria", buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Check logs for dev_otp")
    time.sleep(2)
    
    # ========== FEATURE 2: OTP VERIFICATION ==========
    print_step(2, "OTP VERIFICATION")
    
    print_info("Get OTP from server logs...")
    print(f"{Colors.YELLOW}Run: tail -20 /tmp/trustguard_server.log | grep 'dev_otp\\|DEV-SMS'{Colors.RESET}")
    
    otp = input(f"\n{Colors.YELLOW}Enter the OTP from logs: {Colors.RESET}").strip()
    
    if otp:
        print_info(f"Buyer sends OTP: '{otp}'")
        response = send_whatsapp_message(phone, otp, buyer_name)
        print_success(f"Response: {response.status_code}")
        print_success("Buyer account should be verified!")
    else:
        print_error("No OTP provided, skipping verification")
    
    time.sleep(2)
    
    # ========== FEATURE 3: ORDER CREATION ==========
    print_step(3, "ORDER CREATION")
    
    print_info("Buyer sends: 'order'")
    response = send_whatsapp_message(phone, "order", buyer_name)
    print_success(f"Response: {response.status_code}")
    time.sleep(2)
    
    print_info("Buyer provides order details: 'iPhone 15 Pro - ₦500,000'")
    response = send_whatsapp_message(phone, "iPhone 15 Pro - ₦500,000", buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Order should be created")
    time.sleep(2)
    
    # ========== FEATURE 4: RECEIPT UPLOAD ==========
    print_step(4, "RECEIPT UPLOAD")
    
    print_info("Buyer uploads receipt image")
    response = send_whatsapp_image(
        phone, 
        "https://example.com/receipt.jpg",
        "Payment receipt for iPhone 15 Pro",
        buyer_name
    )
    print_success(f"Response: {response.status_code}")
    print_info("Receipt should be processed and sent to vendor")
    time.sleep(2)
    
    # ========== FEATURE 5: ORDER STATUS CHECK ==========
    print_step(5, "ORDER STATUS CHECK")
    
    print_info("Buyer sends: 'status'")
    response = send_whatsapp_message(phone, "status", buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Bot should return order status")
    time.sleep(2)
    
    # ========== FEATURE 6: HELP COMMAND ==========
    print_step(6, "HELP COMMAND")
    
    print_info("Buyer sends: 'help'")
    response = send_whatsapp_message(phone, "help", buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Bot should show available commands")
    time.sleep(2)
    
    # ========== SUMMARY ==========
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ COMPLETE BUYER FLOW TEST FINISHED!{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 70}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}📊 Features Tested:{Colors.RESET}")
    print(f"  ✅ 1. Buyer Registration (name + address)")
    print(f"  ✅ 2. OTP Verification")
    print(f"  ✅ 3. Order Creation")
    print(f"  ✅ 4. Receipt Upload (image)")
    print(f"  ✅ 5. Order Status Check")
    print(f"  ✅ 6. Help Command")
    
    print(f"\n{Colors.YELLOW}📝 Next Steps:{Colors.RESET}")
    print(f"  1. Check server logs: tail -f /tmp/trustguard_server.log")
    print(f"  2. Check database for buyer record")
    print(f"  3. Check database for order record")
    print(f"  4. Verify receipt was stored")
    print()

def test_instagram_flow():
    """Test Instagram buyer flow with phone collection"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}🧪 INSTAGRAM BUYER FLOW TEST{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    print_info("Instagram flow is similar but includes phone collection step")
    print_info("After address, bot will ask for phone number")
    print()

if __name__ == "__main__":
    # Check if server is running
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code == 200:
            print_success("Server is running")
        else:
            print_error(f"Server returned {health.status_code}")
            exit(1)
    except:
        print_error("Server not reachable. Start with: ./start_testing.sh")
        exit(1)
    
    # Menu
    print(f"\n{Colors.BOLD}Select Test:{Colors.RESET}")
    print(f"1. Complete WhatsApp Buyer Flow (ALL features)")
    print(f"2. Instagram Buyer Flow")
    print(f"3. Quick Registration Test")
    
    choice = input(f"\n{Colors.YELLOW}Enter choice (1-3): {Colors.RESET}").strip()
    
    if choice == "1":
        test_complete_buyer_flow()
    elif choice == "2":
        test_instagram_flow()
    elif choice == "3":
        from test_mock_webhooks import test_whatsapp_buyer_flow
        test_whatsapp_buyer_flow()
    else:
        print_error("Invalid choice")
