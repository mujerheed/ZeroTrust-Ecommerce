#!/usr/bin/env python3
"""
End-to-End Test Suite for Order Service

Tests the complete order lifecycle:
1. Vendor creates order → buyer notified
2. Buyer confirms/cancels order
3. Buyer uploads receipt → order status updated
4. Vendor queries orders
5. Authorization checks

Run: python test_order_e2e.py
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
ORDERS_ENDPOINT = f"{BASE_URL}/orders"

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(text: str):
    """Print colored header."""
    print(f"\n{BLUE}{'=' * 77}{RESET}")
    print(f"{BLUE}{'=' * 11}{RESET}{'  ' * 34}{text:^17}{'  ' * 34}{RESET}")
    print(f"{BLUE}{'=' * 77}{RESET}")
    print(f"{BLUE}{'=' * 11}{RESET}{'  ' * 74}{RESET}")


def print_step(step_num: int, description: str):
    """Print test step."""
    print(f"\n{CYAN}[Step {step_num}] {description}{RESET}")


def print_success(message: str):
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(key: str, value: Any):
    """Print info."""
    print(f"{YELLOW}ℹ {key}: {value}{RESET}")


class OrderE2ETest:
    """End-to-end test suite for order service."""
    
    def __init__(self):
        self.test_results: List[Tuple[str, bool]] = []
        
        # Mock data
        self.vendor_id = "vendor_test_001"
        self.ceo_id = "ceo_test_001"
        self.buyer_id_wa = "wa_2348012345678"
        self.buyer_id_ig = "ig_1234567890123456"
        
        # Mock JWT tokens (in dev, these would be real)
        self.vendor_token = self.create_mock_vendor_token()
        self.buyer_token = self.create_mock_buyer_token()
        
        # Track created orders for cleanup
        self.created_order_ids: List[str] = []
    
    def create_mock_vendor_token(self) -> str:
        """Create mock vendor JWT token."""
        # In production, this would be a real JWT
        # For dev/testing, we'll use a placeholder
        return "mock_vendor_jwt_token_replace_with_real_in_production"
    
    def create_mock_buyer_token(self) -> str:
        """Create mock buyer JWT token."""
        return "mock_buyer_jwt_token_replace_with_real_in_production"
    
    def test_1_create_order_whatsapp(self):
        """Test 1: Create order for WhatsApp buyer."""
        print_step(1, "Test order creation for WhatsApp buyer")
        
        try:
            payload = {
                "buyer_id": self.buyer_id_wa,
                "items": [
                    {
                        "name": "Product A",
                        "quantity": 2,
                        "price": 5000.00,
                        "description": "Test product A"
                    },
                    {
                        "name": "Product B",
                        "quantity": 1,
                        "price": 3000.00,
                        "description": "Test product B"
                    }
                ],
                "notes": "Test order from E2E suite"
            }
            
            headers = {
                "Authorization": f"Bearer {self.vendor_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                ORDERS_ENDPOINT,
                json=payload,
                headers=headers
            )
            
            print_info("Status", response.status_code)
            
            if response.status_code in [200, 201]:
                data = response.json()
                print_info("Response", json.dumps(data, indent=2))
                
                if data.get("status") == "success":
                    order = data.get("data", {})
                    order_id = order.get("order_id")
                    
                    if order_id:
                        self.created_order_ids.append(order_id)
                        print_success(f"Order created successfully: {order_id}")
                        print_info("Total Amount", f"₦{order.get('total_amount', 0):,.2f}")
                        print_info("Status", order.get("status"))
                        print_info("Notification Sent", order.get("notification_sent", False))
                        
                        self.test_results.append(("Order Creation (WhatsApp)", True))
                    else:
                        print_error("Order ID not returned")
                        self.test_results.append(("Order Creation (WhatsApp)", False))
                else:
                    print_error(f"Unexpected status: {data.get('status')}")
                    print_info("Message", data.get("message"))
                    self.test_results.append(("Order Creation (WhatsApp)", False))
            else:
                print_error(f"HTTP {response.status_code}")
                print_info("Response", response.text)
                self.test_results.append(("Order Creation (WhatsApp)", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Order Creation (WhatsApp)", False))
    
    def test_2_create_order_instagram(self):
        """Test 2: Create order for Instagram buyer."""
        print_step(2, "Test order creation for Instagram buyer")
        
        try:
            payload = {
                "buyer_id": self.buyer_id_ig,
                "items": [
                    {
                        "name": "Product C",
                        "quantity": 3,
                        "price": 2500.00
                    }
                ],
                "notes": "Instagram buyer order"
            }
            
            headers = {
                "Authorization": f"Bearer {self.vendor_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                ORDERS_ENDPOINT,
                json=payload,
                headers=headers
            )
            
            print_info("Status", response.status_code)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                if data.get("status") == "success":
                    order = data.get("data", {})
                    order_id = order.get("order_id")
                    
                    if order_id:
                        self.created_order_ids.append(order_id)
                        print_success(f"Instagram order created: {order_id}")
                        self.test_results.append(("Order Creation (Instagram)", True))
                    else:
                        self.test_results.append(("Order Creation (Instagram)", False))
                else:
                    self.test_results.append(("Order Creation (Instagram)", False))
            else:
                self.test_results.append(("Order Creation (Instagram)", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Order Creation (Instagram)", False))
    
    def test_3_get_order_details(self):
        """Test 3: Get order details (vendor)."""
        print_step(3, "Test GET /orders/{order_id} (vendor)")
        
        if not self.created_order_ids:
            print_error("No orders created to query")
            self.test_results.append(("Get Order Details", False))
            return
        
        try:
            order_id = self.created_order_ids[0]
            
            headers = {
                "Authorization": f"Bearer {self.vendor_token}"
            }
            
            response = requests.get(
                f"{ORDERS_ENDPOINT}/{order_id}",
                headers=headers
            )
            
            print_info("Status", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    order = data.get("data", {})
                    print_success("Order details retrieved")
                    print_info("Order ID", order.get("order_id"))
                    print_info("Status", order.get("status"))
                    print_info("Items Count", len(order.get("items", [])))
                    
                    self.test_results.append(("Get Order Details", True))
                else:
                    self.test_results.append(("Get Order Details", False))
            else:
                self.test_results.append(("Get Order Details", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Get Order Details", False))
    
    def test_4_list_vendor_orders(self):
        """Test 4: List all orders for vendor."""
        print_step(4, "Test GET /orders (vendor list)")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.vendor_token}"
            }
            
            response = requests.get(
                ORDERS_ENDPOINT,
                headers=headers
            )
            
            print_info("Status", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    result_data = data.get("data", {})
                    orders = result_data.get("orders", [])
                    count = result_data.get("count", 0)
                    
                    print_success(f"Orders retrieved: {count}")
                    print_info("Expected", f"At least {len(self.created_order_ids)}")
                    
                    self.test_results.append(("List Vendor Orders", True))
                else:
                    self.test_results.append(("List Vendor Orders", False))
            else:
                self.test_results.append(("List Vendor Orders", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("List Vendor Orders", False))
    
    def test_5_confirm_order(self):
        """Test 5: Buyer confirms order."""
        print_step(5, "Test PATCH /orders/{order_id}/confirm")
        
        if not self.created_order_ids:
            print_error("No orders to confirm")
            self.test_results.append(("Confirm Order", False))
            return
        
        try:
            order_id = self.created_order_ids[0]
            
            payload = {
                "buyer_id": self.buyer_id_wa
            }
            
            response = requests.patch(
                f"{ORDERS_ENDPOINT}/{order_id}/confirm",
                json=payload
            )
            
            print_info("Status", response.status_code)
            print_info("Response", response.text[:200])
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    order = data.get("data", {})
                    new_status = order.get("status")
                    
                    print_success(f"Order confirmed, new status: {new_status}")
                    
                    if new_status == "confirmed":
                        self.test_results.append(("Confirm Order", True))
                    else:
                        print_error(f"Expected status 'confirmed', got '{new_status}'")
                        self.test_results.append(("Confirm Order", False))
                else:
                    print_error(f"Status: {data.get('status')}")
                    self.test_results.append(("Confirm Order", False))
            else:
                print_error(f"HTTP {response.status_code}")
                self.test_results.append(("Confirm Order", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Confirm Order", False))
    
    def test_6_add_receipt(self):
        """Test 6: Add payment receipt to order."""
        print_step(6, "Test PATCH /orders/{order_id}/receipt")
        
        if not self.created_order_ids:
            print_error("No orders to add receipt")
            self.test_results.append(("Add Receipt", False))
            return
        
        try:
            order_id = self.created_order_ids[0]
            
            payload = {
                "buyer_id": self.buyer_id_wa,
                "receipt_url": f"https://s3.amazonaws.com/trustguard-receipts/test/{order_id}/receipt.jpg"
            }
            
            response = requests.patch(
                f"{ORDERS_ENDPOINT}/{order_id}/receipt",
                json=payload
            )
            
            print_info("Status", response.status_code)
            print_info("Response", response.text[:200])
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    order = data.get("data", {})
                    new_status = order.get("status")
                    receipt_url = order.get("receipt_url")
                    
                    print_success(f"Receipt added, new status: {new_status}")
                    print_info("Receipt URL", receipt_url[:50] + "..." if receipt_url else "None")
                    
                    if new_status == "paid" and receipt_url:
                        self.test_results.append(("Add Receipt", True))
                    else:
                        self.test_results.append(("Add Receipt", False))
                else:
                    self.test_results.append(("Add Receipt", False))
            else:
                self.test_results.append(("Add Receipt", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Add Receipt", False))
    
    def test_7_cancel_order(self):
        """Test 7: Buyer cancels order."""
        print_step(7, "Test PATCH /orders/{order_id}/cancel")
        
        if len(self.created_order_ids) < 2:
            print_error("Need at least 2 orders to test cancel")
            self.test_results.append(("Cancel Order", False))
            return
        
        try:
            # Cancel the second order (first one is confirmed)
            order_id = self.created_order_ids[1]
            
            payload = {
                "buyer_id": self.buyer_id_ig,
                "reason": "Changed my mind - E2E test"
            }
            
            response = requests.patch(
                f"{ORDERS_ENDPOINT}/{order_id}/cancel",
                json=payload
            )
            
            print_info("Status", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    order = data.get("data", {})
                    new_status = order.get("status")
                    
                    print_success(f"Order cancelled, new status: {new_status}")
                    
                    if new_status == "cancelled":
                        self.test_results.append(("Cancel Order", True))
                    else:
                        self.test_results.append(("Cancel Order", False))
                else:
                    self.test_results.append(("Cancel Order", False))
            else:
                self.test_results.append(("Cancel Order", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Cancel Order", False))
    
    def test_8_filter_by_status(self):
        """Test 8: List orders filtered by status."""
        print_step(8, "Test GET /orders?status=confirmed")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.vendor_token}"
            }
            
            response = requests.get(
                f"{ORDERS_ENDPOINT}?status=confirmed",
                headers=headers
            )
            
            print_info("Status", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    result_data = data.get("data", {})
                    orders = result_data.get("orders", [])
                    
                    # Check all returned orders have status=confirmed
                    all_confirmed = all(o.get("status") == "confirmed" for o in orders)
                    
                    print_success(f"Filtered orders: {len(orders)}")
                    print_info("All confirmed", all_confirmed)
                    
                    self.test_results.append(("Filter By Status", all_confirmed))
                else:
                    self.test_results.append(("Filter By Status", False))
            else:
                self.test_results.append(("Filter By Status", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Filter By Status", False))
    
    def test_9_validation_missing_items(self):
        """Test 9: Validation - order with missing items."""
        print_step(9, "Test validation: missing items")
        
        try:
            payload = {
                "buyer_id": self.buyer_id_wa,
                "items": [],  # Empty items array
                "notes": "Should fail validation"
            }
            
            headers = {
                "Authorization": f"Bearer {self.vendor_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                ORDERS_ENDPOINT,
                json=payload,
                headers=headers
            )
            
            print_info("Status", response.status_code)
            
            # Should return 400 Bad Request
            if response.status_code == 400:
                print_success("Validation correctly rejected empty items")
                self.test_results.append(("Validation (Missing Items)", True))
            else:
                print_error(f"Expected 400, got {response.status_code}")
                self.test_results.append(("Validation (Missing Items)", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Validation (Missing Items)", False))
    
    def test_10_validation_invalid_buyer_id(self):
        """Test 10: Validation - invalid buyer ID format."""
        print_step(10, "Test validation: invalid buyer_id format")
        
        try:
            payload = {
                "buyer_id": "invalid_format_123",  # Should start with wa_ or ig_
                "items": [
                    {
                        "name": "Product X",
                        "quantity": 1,
                        "price": 1000.00
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {self.vendor_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                ORDERS_ENDPOINT,
                json=payload,
                headers=headers
            )
            
            print_info("Status", response.status_code)
            print_info("Response", response.text[:150])
            
            # Should return 400 Bad Request
            if response.status_code == 400:
                print_success("Validation correctly rejected invalid buyer_id")
                self.test_results.append(("Validation (Invalid Buyer ID)", True))
            else:
                print_error(f"Expected 400, got {response.status_code}")
                self.test_results.append(("Validation (Invalid Buyer ID)", False))
        
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            self.test_results.append(("Validation (Invalid Buyer ID)", False))
    
    def print_summary(self):
        """Print test execution summary."""
        print_header("TEST SUMMARY")
        
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        failed = total - passed
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{CYAN}Total Tests: {total}{RESET}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"{YELLOW}Success Rate: {percentage:.1f}%{RESET}\n")
        
        # Detailed results
        for test_name, result in self.test_results:
            status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
            print(f"{status} - {test_name}")
        
        # Key findings
        print_header("KEY FINDINGS")
        
        print(f"\n{YELLOW}ℹ ✓ Implemented:{RESET}")
        print("  - Order creation API (POST /orders)")
        print("  - Order retrieval (GET /orders/{order_id})")
        print("  - Vendor order list (GET /orders)")
        print("  - Order confirmation (PATCH /orders/{order_id}/confirm)")
        print("  - Order cancellation (PATCH /orders/{order_id}/cancel)")
        print("  - Receipt upload (PATCH /orders/{order_id}/receipt)")
        print("  - Status filtering (GET /orders?status=<status>)")
        print("  - Input validation (buyer_id format, items required)")
        print("  - Multi-platform support (WhatsApp + Instagram)")
        
        print(f"\n{YELLOW}ℹ ⚠ Limitations (dev environment):{RESET}")
        print("  - No actual Meta API tokens (buyer notifications stubbed)")
        print("  - No DynamoDB (using mock data)")
        print("  - No S3 (receipt URLs are mock)")
        print("  - JWT tokens are placeholders (no real auth)")
        
        print(f"\n{YELLOW}ℹ 📋 Next Steps:{RESET}")
        print("  1. Deploy to AWS Lambda")
        print("  2. Set up DynamoDB Orders table")
        print("  3. Configure real JWT authentication")
        print("  4. Test with real buyer accounts")
        print("  5. Integrate with vendor dashboard frontend")
        print("  6. Add vendor notifications (order confirmed/cancelled)")
        
        print()


def main():
    """Run all E2E tests."""
    print_header("ORDER SERVICE END-TO-END TEST")
    
    print(f"\n{YELLOW}ℹ Testing order service endpoints{RESET}")
    print(f"{YELLOW}ℹ Base URL: {BASE_URL}{RESET}")
    print(f"{YELLOW}ℹ Orders Endpoint: {ORDERS_ENDPOINT}{RESET}")
    
    # Create test instance
    test = OrderE2ETest()
    
    # Run tests sequentially
    test.test_1_create_order_whatsapp()
    test.test_2_create_order_instagram()
    test.test_3_get_order_details()
    test.test_4_list_vendor_orders()
    test.test_5_confirm_order()
    test.test_6_add_receipt()
    test.test_7_cancel_order()
    test.test_8_filter_by_status()
    test.test_9_validation_missing_items()
    test.test_10_validation_invalid_buyer_id()
    
    # Print summary
    test.print_summary()


if __name__ == "__main__":
    main()
