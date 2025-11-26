#!/usr/bin/env python3
"""
Complete Analytics & Dashboard Test
Tests remaining CEO and Vendor features:
- CEO Analytics Dashboard
- Vendor Analytics
- Chatbot Customization
- Multi-vendor Management
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

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def test_ceo_analytics(ceo_token):
    """Test CEO analytics dashboard"""
    
    print_header("CEO ANALYTICS DASHBOARD")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # 1. Overall metrics
    print_info("Fetching overall metrics...")
    metrics_response = requests.get(
        f"{API_BASE}/ceo/analytics/overview",
        headers=headers,
        timeout=10
    )
    
    if metrics_response.status_code == 200:
        metrics = metrics_response.json().get('data', {})
        print_success("Analytics retrieved!")
        print(f"\n{Colors.YELLOW}Overview:{Colors.RESET}")
        print(f"  Total Orders: {metrics.get('total_orders', 0)}")
        print(f"  Total Revenue: ₦{metrics.get('total_revenue', 0):,}")
        print(f"  Active Buyers: {metrics.get('active_buyers', 0)}")
        print(f"  Active Vendors: {metrics.get('active_vendors', 0)}")
        print(f"  Pending Orders: {metrics.get('pending_orders', 0)}")
        print(f"  Flagged Orders: {metrics.get('flagged_orders', 0)}")
    
    # 2. Revenue trends
    print_info("\nFetching revenue trends...")
    trends_response = requests.get(
        f"{API_BASE}/ceo/analytics/revenue-trends",
        headers=headers,
        params={"period": "30days"},
        timeout=10
    )
    
    if trends_response.status_code == 200:
        print_success("Revenue trends retrieved!")
    
    # 3. Top vendors
    print_info("\nFetching top vendors...")
    vendors_response = requests.get(
        f"{API_BASE}/ceo/analytics/top-vendors",
        headers=headers,
        timeout=10
    )
    
    if vendors_response.status_code == 200:
        print_success("Top vendors retrieved!")

def test_chatbot_customization(ceo_token):
    """Test chatbot customization"""
    
    print_header("CHATBOT CUSTOMIZATION")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # Get current settings
    print_info("Fetching current chatbot settings...")
    get_response = requests.get(
        f"{API_BASE}/ceo/chatbot/settings",
        headers=headers,
        timeout=10
    )
    
    if get_response.status_code == 200:
        current = get_response.json().get('data', {})
        print_success("Current settings retrieved!")
        print(f"\n{Colors.YELLOW}Current Settings:{Colors.RESET}")
        print(f"  Welcome Message: {current.get('welcome_message', 'Default')}")
        print(f"  Tone: {current.get('tone', 'professional')}")
        print(f"  Language: {current.get('language', 'en')}")
    
    # Update settings
    print_info("\nUpdating chatbot settings...")
    update_response = requests.put(
        f"{API_BASE}/ceo/chatbot/settings",
        headers=headers,
        json={
            "welcome_message": "Welcome to TrustGuard! 🛡️ Your trusted e-commerce partner.",
            "tone": "friendly",
            "language": "en",
            "auto_responses": {
                "greeting": "Hi! How can I help you today?",
                "order_confirmed": "Your order has been confirmed! 🎉",
                "receipt_received": "Receipt received! Our vendor will review it shortly."
            }
        },
        timeout=10
    )
    
    if update_response.status_code == 200:
        print_success("Chatbot settings updated!")
        print_info("Changes will apply to new conversations")

def test_vendor_management(ceo_token):
    """Test vendor management"""
    
    print_header("VENDOR MANAGEMENT")
    
    headers = {"Authorization": f"Bearer {ceo_token}"}
    
    # 1. List all vendors
    print_info("Fetching all vendors...")
    vendors_response = requests.get(
        f"{API_BASE}/ceo/vendors",
        headers=headers,
        timeout=10
    )
    
    if vendors_response.status_code == 200:
        vendors = vendors_response.json().get('data', [])
        print_success(f"Found {len(vendors)} vendor(s)")
        
        for i, vendor in enumerate(vendors, 1):
            print(f"\n{Colors.YELLOW}Vendor {i}:{Colors.RESET}")
            print(f"  ID: {vendor.get('vendor_id')}")
            print(f"  Name: {vendor.get('name')}")
            print(f"  Phone: {vendor.get('phone')}")
            print(f"  Status: {vendor.get('status')}")
            print(f"  Orders Handled: {vendor.get('orders_count', 0)}")
    
    # 2. Create new vendor
    print_info("\nCreating new vendor...")
    create_response = requests.post(
        f"{API_BASE}/ceo/vendors",
        headers=headers,
        json={
            "name": "Test Vendor 2",
            "phone": "+2348034567890",
            "email": "vendor2@trustguard.com"
        },
        timeout=10
    )
    
    if create_response.status_code in [200, 201]:
        print_success("New vendor created!")
        vendor_data = create_response.json().get('data', {})
        print_info(f"Vendor ID: {vendor_data.get('vendor_id')}")

def test_vendor_analytics(vendor_token):
    """Test vendor analytics"""
    
    print_header("VENDOR ANALYTICS")
    
    headers = {"Authorization": f"Bearer {vendor_token}"}
    
    # Vendor performance metrics
    print_info("Fetching vendor performance...")
    performance_response = requests.get(
        f"{API_BASE}/vendor/analytics/performance",
        headers=headers,
        timeout=10
    )
    
    if performance_response.status_code == 200:
        perf = performance_response.json().get('data', {})
        print_success("Performance metrics retrieved!")
        print(f"\n{Colors.YELLOW}Performance:{Colors.RESET}")
        print(f"  Orders Reviewed: {perf.get('orders_reviewed', 0)}")
        print(f"  Orders Approved: {perf.get('orders_approved', 0)}")
        print(f"  Orders Flagged: {perf.get('orders_flagged', 0)}")
        print(f"  Average Review Time: {perf.get('avg_review_time', 0)} min")
        print(f"  Approval Rate: {perf.get('approval_rate', 0)}%")

def main():
    print(f"\n{Colors.BOLD}🧪 COMPLETE ANALYTICS & DASHBOARD TEST{Colors.RESET}\n")
    
    # Check server
    try:
        health = requests.get(f"{API_BASE}/", timeout=5)
        if health.status_code != 200:
            print(f"{Colors.RED}❌ Server not running!{Colors.RESET}")
            return
    except:
        print(f"{Colors.RED}❌ Server not reachable. Start with: ./start_testing.sh{Colors.RESET}")
        return
    
    print(f"{Colors.BOLD}Select Test:{Colors.RESET}")
    print(f"1. CEO Analytics Dashboard")
    print(f"2. Chatbot Customization")
    print(f"3. Vendor Management")
    print(f"4. Vendor Analytics")
    print(f"5. Complete Flow (All Tests)")
    
    choice = input(f"\n{Colors.YELLOW}Enter choice (1-5): {Colors.RESET}").strip()
    
    # Get tokens
    if choice in ["1", "2", "3", "5"]:
        ceo_token = input(f"{Colors.YELLOW}Enter CEO token: {Colors.RESET}").strip()
        if not ceo_token:
            print(f"{Colors.RED}❌ CEO token required{Colors.RESET}")
            return
    
    if choice in ["4", "5"]:
        vendor_token = input(f"{Colors.YELLOW}Enter Vendor token: {Colors.RESET}").strip()
        if not vendor_token:
            print(f"{Colors.RED}❌ Vendor token required{Colors.RESET}")
            return
    
    # Run tests
    if choice == "1":
        test_ceo_analytics(ceo_token)
    elif choice == "2":
        test_chatbot_customization(ceo_token)
    elif choice == "3":
        test_vendor_management(ceo_token)
    elif choice == "4":
        test_vendor_analytics(vendor_token)
    elif choice == "5":
        test_ceo_analytics(ceo_token)
        time.sleep(2)
        test_chatbot_customization(ceo_token)
        time.sleep(2)
        test_vendor_management(ceo_token)
        time.sleep(2)
        test_vendor_analytics(vendor_token)
    else:
        print(f"{Colors.RED}❌ Invalid choice{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}✅ Test complete!{Colors.RESET}\n")

if __name__ == "__main__":
    main()
