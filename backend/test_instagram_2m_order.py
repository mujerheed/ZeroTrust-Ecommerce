#!/usr/bin/env python3
"""
Instagram Existing Buyer Test - ₦2M Order
Tests existing buyer placing a high-value order via Instagram
"""

import requests
import json
import time
import hmac
import hashlib
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

def send_instagram_message(instagram_psid, message_text, buyer_name="Jane Smith"):
    """Simulate Instagram buyer sending a message"""
    
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "111846985278796",  # Your Instagram Page ID
            "time": int(time.time()),
            "messaging": [{
                "sender": {"id": instagram_psid},
                "recipient": {"id": "111846985278796"},
                "timestamp": int(time.time() * 1000),
                "message": {
                    "mid": f"ig_mid_{int(time.time())}",
                    "text": message_text
                }
            }]
        }]
    }
    
    payload_str = json.dumps(payload)
    signature = create_signature(payload_str, APP_SECRET)
    
    response = requests.post(
        f"{API_BASE}/integrations/webhook/instagram",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature
        },
        timeout=10
    )
    
    return response

def send_instagram_image(instagram_psid, image_url, buyer_name="Jane Smith"):
    """Simulate Instagram buyer sending an image"""
    
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "111846985278796",
            "time": int(time.time()),
            "messaging": [{
                "sender": {"id": instagram_psid},
                "recipient": {"id": "111846985278796"},
                "timestamp": int(time.time() * 1000),
                "message": {
                    "mid": f"ig_mid_{int(time.time())}",
                    "attachments": [{
                        "type": "image",
                        "payload": {
                            "url": image_url
                        }
                    }]
                }
            }]
        }]
    }
    
    payload_str = json.dumps(payload)
    signature = create_signature(payload_str, APP_SECRET)
    
    response = requests.post(
        f"{API_BASE}/integrations/webhook/instagram",
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

def test_existing_buyer_order():
    """Test existing Instagram buyer placing ₦2M order"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}📸 INSTAGRAM EXISTING BUYER - ₦2M ORDER{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    # Use existing buyer (phone-based ID)
    instagram_psid = "2348023456789"  # Original PSID
    buyer_phone = "+2348023456789"
    buyer_name = "Jane Smith"
    
    print_info(f"Buyer: {buyer_name}")
    print_info(f"Instagram PSID: {instagram_psid}")
    print_info(f"Phone-based ID: ig_{buyer_phone.replace('+', '')}")
    
    # Step 1: Buyer says "order"
    print_step(1, "Buyer Initiates Order")
    
    print_info("Buyer sends: 'order'")
    response = send_instagram_message(instagram_psid, "order", buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Bot should ask for order details")
    time.sleep(2)
    
    # Step 2: Buyer provides order details
    print_step(2, "Buyer Provides Order Details (₦2M)")
    
    order_details = """MacBook Pro M3 Max 16" - ₦2,000,000
Specs:
- 16GB RAM
- 1TB SSD
- Space Black
- AppleCare+ included"""
    
    print_info(f"Buyer sends:\n{order_details}")
    response = send_instagram_message(instagram_psid, order_details, buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Order should be created")
    time.sleep(2)
    
    # Step 3: Bot asks for receipt
    print_step(3, "Bot Requests Payment Receipt")
    
    print_info("Bot should ask: 'Please upload your payment receipt'")
    time.sleep(2)
    
    # Step 4: Buyer uploads receipt
    print_step(4, "Buyer Uploads Receipt (₦2M)")
    
    print_info("Buyer uploads receipt image...")
    response = send_instagram_image(
        instagram_psid,
        "https://example.com/receipt_2m.jpg",
        buyer_name
    )
    print_success(f"Response: {response.status_code}")
    print_info("Receipt should be processed")
    time.sleep(2)
    
    # Step 5: Check order status
    print_step(5, "Buyer Checks Order Status")
    
    print_info("Buyer sends: 'status'")
    response = send_instagram_message(instagram_psid, "status", buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Bot should return order details")
    time.sleep(2)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ INSTAGRAM EXISTING BUYER TEST COMPLETE!{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 70}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}📊 Order Summary:{Colors.RESET}")
    print(f"  • Buyer: {buyer_name} (existing)")
    print(f"  • Platform: Instagram")
    print(f"  • Item: MacBook Pro M3 Max 16\"")
    print(f"  • Amount: ₦2,000,000")
    print(f"  • Receipt: Uploaded")
    
    print(f"\n{Colors.YELLOW}📝 Next Steps:{Colors.RESET}")
    print(f"  1. Check server logs: tail -f /tmp/trustguard_server.log")
    print(f"  2. Verify order in database")
    print(f"  3. Check vendor receives notification")
    print(f"  4. Vendor reviews receipt")
    print(f"  5. Vendor approves/flags order")
    print()

def create_existing_buyer():
    """Create the existing buyer first"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}👤 CREATING EXISTING BUYER{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    instagram_psid = "2348023456789"
    buyer_phone = "+2348023456789"
    buyer_name = "Jane Smith"
    
    print_info("Simulating buyer registration flow...")
    
    # Step 1: Hi
    print_step(1, "Initial Contact")
    response = send_instagram_message(instagram_psid, "hi", buyer_name)
    print_success(f"Response: {response.status_code}")
    time.sleep(2)
    
    # Step 2: Name
    print_step(2, "Provide Name")
    response = send_instagram_message(instagram_psid, buyer_name, buyer_name)
    print_success(f"Response: {response.status_code}")
    time.sleep(2)
    
    # Step 3: Address
    print_step(3, "Provide Address")
    response = send_instagram_message(instagram_psid, "456 Victoria Island, Lagos, Nigeria", buyer_name)
    print_success(f"Response: {response.status_code}")
    time.sleep(2)
    
    # Step 4: Phone
    print_step(4, "Provide Phone")
    response = send_instagram_message(instagram_psid, buyer_phone, buyer_name)
    print_success(f"Response: {response.status_code}")
    print_info("Check logs for OTP")
    time.sleep(2)
    
    # Step 5: OTP
    print_step(5, "Verify OTP")
    otp = input(f"\n{Colors.YELLOW}Enter OTP from logs: {Colors.RESET}").strip()
    
    if otp:
        response = send_instagram_message(instagram_psid, otp, buyer_name)
        print_success(f"Response: {response.status_code}")
        print_success("Buyer verified and ready!")
    else:
        print_info("Skipping OTP verification")
    
    print(f"\n{Colors.GREEN}✅ Existing buyer created!{Colors.RESET}\n")

if __name__ == "__main__":
    # Check if server is running
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code != 200:
            print(f"{Colors.RED}❌ Server not running!{Colors.RESET}")
            exit(1)
    except:
        print(f"{Colors.RED}❌ Server not reachable. Start with: ./start_testing.sh{Colors.RESET}")
        exit(1)
    
    print(f"\n{Colors.BOLD}Select Test:{Colors.RESET}")
    print(f"1. Create Existing Buyer (Jane Smith)")
    print(f"2. Existing Buyer Places ₦2M Order")
    print(f"3. Complete Flow (Create + Order)")
    
    choice = input(f"\n{Colors.YELLOW}Enter choice (1-3): {Colors.RESET}").strip()
    
    if choice == "1":
        create_existing_buyer()
    elif choice == "2":
        test_existing_buyer_order()
    elif choice == "3":
        create_existing_buyer()
        time.sleep(2)
        test_existing_buyer_order()
    else:
        print(f"{Colors.RED}❌ Invalid choice{Colors.RESET}")
