#!/usr/bin/env python3
"""
Vendor Dashboard & CEO Escalation Test
Tests:
1. Vendor views pending orders
2. Vendor approves order (amount matches)
3. Vendor flags order (discrepancy detected)
4. CEO receives escalation
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_step(step, text):
    print(f"\n{Colors.BOLD}Step {step}: {text}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def test_vendor_dashboard():
    """Test vendor viewing pending orders"""
    
    print_header("VENDOR DASHBOARD - PENDING ORDERS")
    
    # First, create a vendor and get token
    print_step(1, "Login as Vendor")
    
    vendor_phone = "+2348023456789"
    
    # Request OTP
    print_info(f"Requesting OTP for vendor: {vendor_phone}")
    otp_response = requests.post(
        f"{API_BASE}/auth/vendor/login",
        json={"phone": vendor_phone},
        timeout=10
    )
    
    if otp_response.status_code in [200, 201]:
        data = otp_response.json()
        vendor_id = data.get('data', {}).get('vendor_id')
        dev_otp = data.get('data', {}).get('dev_otp')
        
        print_success(f"Vendor ID: {vendor_id}")
        
        if dev_otp:
            print_info(f"Dev OTP: {dev_otp}")
            
            # Verify OTP
            verify_response = requests.post(
                f"{API_BASE}/auth/verify-otp",
                json={"user_id": vendor_id, "otp": dev_otp},
                timeout=10
            )
            
            if verify_response.status_code == 200:
                token = verify_response.json().get('data', {}).get('token')
                print_success("Vendor logged in!")
                
                # Get pending orders
                print_step(2, "View Pending Orders")
                
                headers = {"Authorization": f"Bearer {token}"}
                orders_response = requests.get(
                    f"{API_BASE}/vendor/orders/pending",
                    headers=headers,
                    timeout=10
                )
                
                if orders_response.status_code == 200:
                    orders = orders_response.json().get('data', [])
                    print_success(f"Found {len(orders)} pending order(s)")
                    
                    for i, order in enumerate(orders, 1):
                        print(f"\n{Colors.YELLOW}Order {i}:{Colors.RESET}")
                        print(f"  Order ID: {order.get('order_id')}")
                        print(f"  Buyer: {order.get('buyer_name')}")
                        print(f"  Amount: ₦{order.get('total_amount'):,}")
                        print(f"  Items: {order.get('items')}")
                        print(f"  Receipt: {'✅ Uploaded' if order.get('receipt_url') else '❌ Pending'}")
                    
                    return token, orders
                else:
                    print_error(f"Failed to get orders: {orders_response.text}")
            else:
                print_error("OTP verification failed")
        else:
            print_error("No dev_otp (check ENVIRONMENT=dev)")
    else:
        print_error(f"Login failed: {otp_response.text}")
    
    return None, []


def test_vendor_approve_order(token, order_id):
    """Test vendor approving an order (amount matches)"""
    
    print_header("VENDOR APPROVES ORDER (Amount Matches)")
    
    print_step(1, f"Approve Order: {order_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    approve_response = requests.post(
        f"{API_BASE}/vendor/orders/{order_id}/approve",
        headers=headers,
        json={
            "notes": "Receipt verified. Amount matches order total.",
            "verified_amount": 2000000  # Matches order
        },
        timeout=10
    )
    
    if approve_response.status_code in [200, 201]:
        print_success("Order approved!")
        data = approve_response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        print_success("Buyer will be notified of approval")
    else:
        print_error(f"Approval failed: {approve_response.text}")


def test_vendor_flag_order(token, order_id):
    """Test vendor flagging an order (discrepancy detected)"""
    
    print_header("VENDOR FLAGS ORDER (Discrepancy Detected)")
    
    print_step(1, f"Flag Order: {order_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    flag_response = requests.post(
        f"{API_BASE}/vendor/orders/{order_id}/flag",
        headers=headers,
        json={
            "reason": "amount_mismatch",
            "details": "Receipt shows ₦1,800,000 but order is for ₦2,000,000. Discrepancy of ₦200,000.",
            "receipt_amount": 1800000,  # Amount on receipt
            "order_amount": 2000000,     # Amount in order
            "severity": "high"
        },
        timeout=10
    )
    
    if flag_response.status_code in [200, 201]:
        print_success("Order flagged!")
        data = flag_response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        print_success("CEO will be notified for escalation")
        
        # Show escalation details
        print(f"\n{Colors.RED}🚨 ESCALATION TRIGGERED:{Colors.RESET}")
        print(f"  Reason: Amount Mismatch")
        print(f"  Order Amount: ₦2,000,000")
        print(f"  Receipt Amount: ₦1,800,000")
        print(f"  Discrepancy: ₦200,000")
        print(f"  Severity: HIGH")
        print(f"  Status: Pending CEO Review")
    else:
        print_error(f"Flag failed: {flag_response.text}")


def test_ceo_view_escalations(ceo_token):
    """Test CEO viewing flagged orders"""
    
    print_header("CEO DASHBOARD - ESCALATIONS")
    
    print_step(1, "View Flagged Orders")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    escalations_response = requests.get(
        f"{API_BASE}/ceo/orders/flagged",
        headers=headers,
        timeout=10
    )
    
    if escalations_response.status_code == 200:
        escalations = escalations_response.json().get('data', [])
        print_success(f"Found {len(escalations)} flagged order(s)")
        
        for i, esc in enumerate(escalations, 1):
            print(f"\n{Colors.RED}Escalation {i}:{Colors.RESET}")
            print(f"  Order ID: {esc.get('order_id')}")
            print(f"  Buyer: {esc.get('buyer_name')}")
            print(f"  Vendor: {esc.get('vendor_name')}")
            print(f"  Reason: {esc.get('flag_reason')}")
            print(f"  Details: {esc.get('flag_details')}")
            print(f"  Severity: {esc.get('severity')}")
            print(f"  Flagged At: {esc.get('flagged_at')}")
    else:
        print_error(f"Failed to get escalations: {escalations_response.text}")


def main():
    print(f"\n{Colors.BOLD}🎯 VENDOR DASHBOARD & CEO ESCALATION TEST{Colors.RESET}\n")
    
    # Check server
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code != 200:
            print_error("Server not running!")
            return
    except:
        print_error("Server not reachable. Start with: ./start_testing.sh")
        return
    
    print(f"{Colors.BOLD}Select Test:{Colors.RESET}")
    print(f"1. Vendor Dashboard (View Pending Orders)")
    print(f"2. Vendor Approves Order (Amount Matches)")
    print(f"3. Vendor Flags Order (Discrepancy)")
    print(f"4. CEO Views Escalations")
    print(f"5. Complete Flow (All Tests)")
    
    choice = input(f"\n{Colors.YELLOW}Enter choice (1-5): {Colors.RESET}").strip()
    
    if choice == "1":
        test_vendor_dashboard()
    
    elif choice == "2":
        token, orders = test_vendor_dashboard()
        if token and orders:
            order_id = orders[0].get('order_id')
            time.sleep(2)
            test_vendor_approve_order(token, order_id)
    
    elif choice == "3":
        token, orders = test_vendor_dashboard()
        if token and orders:
            order_id = orders[0].get('order_id')
            time.sleep(2)
            test_vendor_flag_order(token, order_id)
    
    elif choice == "4":
        # Need CEO token
        print_info("First, get CEO token...")
        ceo_token = input(f"{Colors.YELLOW}Enter CEO token: {Colors.RESET}").strip()
        if ceo_token:
            test_ceo_view_escalations(ceo_token)
    
    elif choice == "5":
        # Complete flow
        print_info("Running complete flow...")
        
        # Vendor dashboard
        token, orders = test_vendor_dashboard()
        
        if token and orders:
            order_id = orders[0].get('order_id')
            
            time.sleep(2)
            
            # Flag order (discrepancy)
            test_vendor_flag_order(token, order_id)
            
            time.sleep(2)
            
            # CEO views escalation
            print_info("\nFor CEO escalation view, you need CEO token")
            print_info("Run: python3 test_ceo_registration.py to get CEO token")
    
    else:
        print_error("Invalid choice")
    
    print(f"\n{Colors.GREEN}✅ Test complete!{Colors.RESET}\n")


if __name__ == "__main__":
    main()
