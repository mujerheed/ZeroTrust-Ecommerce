#!/usr/bin/env python3
"""
Receipt Upload & Order Summary Test
Tests:
1. Receipt upload (with sample images)
2. Order summary PDF generation
3. Download completed order summary
"""

import requests
import json
import time
import os
from pathlib import Path

API_BASE = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

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

def test_receipt_upload():
    """Test receipt upload with sample images"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}🧪 RECEIPT UPLOAD TEST{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    # Check for sample receipts
    artifacts_dir = Path("/home/secure/.gemini/antigravity/brain/683bba3c-47ea-4100-a86a-194ac18119d9")
    receipt_files = list(artifacts_dir.glob("sample_receipt_*.webp"))
    
    if not receipt_files:
        print_error("No sample receipt images found!")
        print_info("Generate them first with the image generation tool")
        return
    
    print_success(f"Found {len(receipt_files)} sample receipt(s)")
    
    # Test with first receipt
    receipt_path = receipt_files[0]
    print_info(f"Using: {receipt_path.name}")
    
    print_step(1, "Upload Receipt via API")
    
    # Create a test order first
    order_data = {
        "buyer_id": "wa_2348012345678",
        "vendor_id": "vendor_test123",
        "items": [
            {
                "name": "iPhone 15 Pro Max",
                "price": 850000,
                "quantity": 1
            }
        ],
        "total_amount": 850000,
        "delivery_address": "123 Ikeja Road, Lagos"
    }
    
    print_info("Creating test order...")
    try:
        order_response = requests.post(
            f"{API_BASE}/orders/create",
            json=order_data,
            timeout=10
        )
        
        if order_response.status_code in [200, 201]:
            order_id = order_response.json().get('data', {}).get('order_id')
            print_success(f"Order created: {order_id}")
            
            # Upload receipt
            print_info("Uploading receipt image...")
            
            with open(receipt_path, 'rb') as f:
                files = {'receipt': (receipt_path.name, f, 'image/webp')}
                data = {'order_id': order_id}
                
                upload_response = requests.post(
                    f"{API_BASE}/orders/{order_id}/receipt",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if upload_response.status_code in [200, 201]:
                    print_success("Receipt uploaded successfully!")
                    receipt_data = upload_response.json()
                    print_info(f"Response: {json.dumps(receipt_data, indent=2)}")
                else:
                    print_error(f"Upload failed: {upload_response.status_code}")
                    print_info(f"Response: {upload_response.text}")
        else:
            print_error(f"Order creation failed: {order_response.status_code}")
            print_info(f"Response: {order_response.text}")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_order_summary_download():
    """Test order summary PDF generation and download"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}📄 ORDER SUMMARY DOWNLOAD TEST{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    print_step(1, "Get Completed Orders")
    
    try:
        # Get list of orders
        orders_response = requests.get(
            f"{API_BASE}/orders?status=completed",
            timeout=10
        )
        
        if orders_response.status_code == 200:
            orders = orders_response.json().get('data', [])
            
            if orders:
                order_id = orders[0].get('order_id')
                print_success(f"Found completed order: {order_id}")
                
                print_step(2, "Generate Order Summary PDF")
                
                # Generate PDF
                pdf_response = requests.get(
                    f"{API_BASE}/orders/{order_id}/summary",
                    timeout=30
                )
                
                if pdf_response.status_code == 200:
                    # Save PDF
                    pdf_path = f"/tmp/order_summary_{order_id}.pdf"
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_response.content)
                    
                    print_success(f"PDF downloaded: {pdf_path}")
                    print_info(f"Size: {len(pdf_response.content)} bytes")
                    print_info(f"Open with: xdg-open {pdf_path}")
                else:
                    print_error(f"PDF generation failed: {pdf_response.status_code}")
            else:
                print_info("No completed orders found")
                print_info("Create and complete an order first")
        else:
            print_error(f"Failed to get orders: {orders_response.status_code}")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_mock_receipt_upload():
    """Test receipt upload via mock webhook (simpler)"""
    
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}📸 MOCK WEBHOOK RECEIPT UPLOAD{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    print_info("This simulates a buyer sending a receipt image via WhatsApp")
    
    from test_mock_webhooks import send_whatsapp_image
    
    phone = "+2348012345678"
    
    # Send mock receipt
    print_info("Sending mock receipt image...")
    response = send_whatsapp_image(
        phone,
        "https://example.com/receipt.jpg",
        "Payment receipt for iPhone 15 Pro",
        "John Doe"
    )
    
    if response.status_code == 200:
        print_success("Mock receipt sent successfully!")
        print_info("Check server logs for processing details")
        print_info("Run: tail -20 /tmp/trustguard_server.log | grep -i receipt")
    else:
        print_error(f"Failed: {response.status_code}")

if __name__ == "__main__":
    # Check if server is running
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code != 200:
            print_error("Server not running!")
            exit(1)
    except:
        print_error("Server not reachable. Start with: ./start_testing.sh")
        exit(1)
    
    print(f"\n{Colors.BOLD}Select Test:{Colors.RESET}")
    print(f"1. Upload Receipt (Direct API)")
    print(f"2. Download Order Summary PDF")
    print(f"3. Mock Webhook Receipt Upload (Recommended)")
    print(f"4. Run All Tests")
    
    choice = input(f"\n{Colors.YELLOW}Enter choice (1-4): {Colors.RESET}").strip()
    
    if choice == "1":
        test_receipt_upload()
    elif choice == "2":
        test_order_summary_download()
    elif choice == "3":
        test_mock_receipt_upload()
    elif choice == "4":
        test_mock_receipt_upload()
        time.sleep(2)
        test_receipt_upload()
        time.sleep(2)
        test_order_summary_download()
    else:
        print_error("Invalid choice")
    
    print(f"\n{Colors.GREEN}✅ Test complete!{Colors.RESET}\n")
