#!/usr/bin/env python3
"""
Mock WhatsApp Webhook Sender
Simulates Meta sending webhooks to test buyer flows WITHOUT business verification
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
    RESET = '\033[0m'

def create_signature(payload_str, secret):
    """Create HMAC signature like Meta does"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def send_whatsapp_message(phone_number, message_text, buyer_name="Test Buyer"):
    """Simulate WhatsApp buyer sending a message"""
    
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
    
    print(f"{Colors.BLUE}📤 Sending: {message_text}{Colors.RESET}")
    
    response = requests.post(
        f"{API_BASE}/integrations/webhook/whatsapp",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature
        },
        timeout=10
    )
    
    print(f"{Colors.GREEN}✅ Response: {response.status_code}{Colors.RESET}")
    if response.status_code != 200:
        print(f"{Colors.YELLOW}Response body: {response.text}{Colors.RESET}")
    
    return response

def test_whatsapp_buyer_flow():
    """Test complete WhatsApp buyer registration flow"""
    
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BLUE}🧪 MOCK WHATSAPP BUYER FLOW TEST{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")
    
    phone = "+2348012345678"
    
    # Step 1: Buyer says "hi"
    print(f"{Colors.YELLOW}Step 1: Buyer initiates conversation{Colors.RESET}")
    send_whatsapp_message(phone, "hi", "John Doe")
    print(f"{Colors.GREEN}✅ Bot should ask for name{Colors.RESET}\n")
    time.sleep(2)
    
    # Step 2: Buyer provides name
    print(f"{Colors.YELLOW}Step 2: Buyer provides name{Colors.RESET}")
    send_whatsapp_message(phone, "John Doe")
    print(f"{Colors.GREEN}✅ Bot should ask for address{Colors.RESET}\n")
    time.sleep(2)
    
    # Step 3: Buyer provides address
    print(f"{Colors.YELLOW}Step 3: Buyer provides address{Colors.RESET}")
    send_whatsapp_message(phone, "123 Ikeja Road, Lagos, Nigeria")
    print(f"{Colors.GREEN}✅ Bot should send OTP{Colors.RESET}\n")
    time.sleep(2)
    
    # Step 4: Check logs for OTP
    print(f"{Colors.YELLOW}Step 4: Check server logs for OTP{Colors.RESET}")
    print(f"{Colors.BLUE}Run: tail -20 /tmp/trustguard_server.log | grep OTP{Colors.RESET}\n")
    
    print(f"{Colors.GREEN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.GREEN}✅ MOCK WEBHOOK TEST COMPLETE!{Colors.RESET}")
    print(f"{Colors.GREEN}{'=' * 70}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}📊 Next Steps:{Colors.RESET}")
    print(f"1. Check server logs: tail -f /tmp/trustguard_server.log")
    print(f"2. Find dev_otp in logs")
    print(f"3. Send OTP: python3 -c 'from test_mock_webhooks import send_whatsapp_message; send_whatsapp_message(\"+2348012345678\", \"YOUR_OTP_HERE\")'")
    print()

if __name__ == "__main__":
    # Check if server is running
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code == 200:
            print(f"{Colors.GREEN}✅ Server is running{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠️  Server returned {health.status_code}{Colors.RESET}")
    except:
        print(f"{Colors.YELLOW}❌ Server not reachable. Start with: ./start_testing.sh{Colors.RESET}")
        exit(1)
    
    # Run the test
    test_whatsapp_buyer_flow()
