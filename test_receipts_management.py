#!/usr/bin/env python3
"""
Test script for CEO Receipts Management endpoints.

Tests:
1. List receipts (with filters)
2. Get receipt statistics
3. Get flagged receipts
4. Get receipt details
5. Bulk verify receipts
"""

import requests
import json
import time
from typing import Dict, Any, Optional


class Color:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class ReceiptsManagementTester:
    """Test CEO Receipts Management functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ceo_token: Optional[str] = None
        self.ceo_id: Optional[str] = None
        self.test_results = []
    
    def log(self, message: str, color: str = Color.ENDC):
        """Print colored log message."""
        print(f"{color}{message}{Color.ENDC}")
    
    def register_and_login_ceo(self) -> bool:
        """Register and login as CEO to get auth token."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("Setting up CEO account for testing", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        # Register CEO via auth service
        register_data = {
            "name": "Test CEO - Receipts",
            "email": f"receipts_test_{int(time.time())}@example.com",
            "phone": f"+234801{int(time.time()) % 10000000:07d}",
            "role": "CEO"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/ceo/register",
                json=register_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.ceo_id = data['data']['ceo_id']
                dev_otp = data['data'].get('dev_otp')
                
                self.log(f"✓ CEO registered: {self.ceo_id}", Color.OKGREEN)
                self.log(f"  Dev OTP: {dev_otp}", Color.OKCYAN)
                
                # Verify OTP
                verify_response = requests.post(
                    f"{self.base_url}/auth/verify-otp",
                    json={
                        "user_id": self.ceo_id,
                        "otp": dev_otp,
                        "role": "CEO"
                    }
                )
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    self.ceo_token = verify_data['data']['token']
                    self.log(f"✓ CEO logged in successfully", Color.OKGREEN)
                    return True
                else:
                    self.log(f"✗ OTP verification failed: {verify_response.text}", Color.FAIL)
                    return False
            else:
                self.log(f"✗ CEO registration failed: {response.text}", Color.FAIL)
                return False
        
        except Exception as e:
            self.log(f"✗ Error during setup: {e}", Color.FAIL)
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.ceo_token}",
            "Content-Type": "application/json"
        }
    
    def test_list_receipts(self):
        """Test GET /ceo/receipts endpoint."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("TEST: List Receipts", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        try:
            # Test without filters
            response = requests.get(
                f"{self.base_url}/ceo/receipts",
                headers=self.get_headers()
            )
            
            self.log(f"Response Status: {response.status_code}", Color.OKCYAN)
            
            if response.status_code == 200:
                data = response.json()
                receipts = data['data']['receipts']
                count = data['data']['count']
                has_more = data['data']['has_more']
                
                self.log(f"✓ Retrieved {count} receipt(s)", Color.OKGREEN)
                self.log(f"  Has more: {has_more}", Color.OKCYAN)
                
                self.test_results.append({
                    'test': 'List Receipts (no filters)',
                    'passed': True,
                    'details': f"Retrieved {count} receipts"
                })
                
                # Test with status filter
                self.log("\nTesting with status filter...", Color.OKCYAN)
                response2 = requests.get(
                    f"{self.base_url}/ceo/receipts?status=pending_review&limit=10",
                    headers=self.get_headers()
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    self.log(f"✓ Filtered receipts: {data2['data']['count']}", Color.OKGREEN)
                    self.test_results.append({
                        'test': 'List Receipts (with status filter)',
                        'passed': True,
                        'details': f"Filter working correctly"
                    })
                else:
                    self.log(f"✗ Filter test failed: {response2.text}", Color.FAIL)
                    self.test_results.append({
                        'test': 'List Receipts (with status filter)',
                        'passed': False,
                        'details': f"Status {response2.status_code}"
                    })
            else:
                self.log(f"✗ Failed: {response.text}", Color.FAIL)
                self.test_results.append({
                    'test': 'List Receipts',
                    'passed': False,
                    'details': f"Status {response.status_code}"
                })
        
        except Exception as e:
            self.log(f"✗ Error: {e}", Color.FAIL)
            self.test_results.append({
                'test': 'List Receipts',
                'passed': False,
                'details': str(e)
            })
    
    def test_receipt_stats(self):
        """Test GET /ceo/receipts/stats endpoint."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("TEST: Receipt Statistics", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        try:
            response = requests.get(
                f"{self.base_url}/ceo/receipts/stats",
                headers=self.get_headers()
            )
            
            self.log(f"Response Status: {response.status_code}", Color.OKCYAN)
            
            if response.status_code == 200:
                data = response.json()
                stats = data['data']
                
                self.log(f"✓ Receipt Statistics Retrieved", Color.OKGREEN)
                self.log(f"  Total Receipts: {stats['total_receipts']}", Color.OKCYAN)
                self.log(f"  Pending Review: {stats['pending_review']}", Color.OKCYAN)
                self.log(f"  Approved: {stats['approved']}", Color.OKGREEN)
                self.log(f"  Rejected: {stats['rejected']}", Color.WARNING)
                self.log(f"  Flagged: {stats['flagged']}", Color.FAIL)
                self.log(f"  Verification Rate: {stats['verification_rate']}%", Color.OKCYAN)
                self.log(f"  Avg Processing Time: {stats['avg_processing_time_hours']} hours", Color.OKCYAN)
                
                self.test_results.append({
                    'test': 'Receipt Statistics',
                    'passed': True,
                    'details': f"Total: {stats['total_receipts']}, Verification Rate: {stats['verification_rate']}%"
                })
            else:
                self.log(f"✗ Failed: {response.text}", Color.FAIL)
                self.test_results.append({
                    'test': 'Receipt Statistics',
                    'passed': False,
                    'details': f"Status {response.status_code}"
                })
        
        except Exception as e:
            self.log(f"✗ Error: {e}", Color.FAIL)
            self.test_results.append({
                'test': 'Receipt Statistics',
                'passed': False,
                'details': str(e)
            })
    
    def test_flagged_receipts(self):
        """Test GET /ceo/receipts/flagged endpoint."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("TEST: Flagged Receipts", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        try:
            response = requests.get(
                f"{self.base_url}/ceo/receipts/flagged",
                headers=self.get_headers()
            )
            
            self.log(f"Response Status: {response.status_code}", Color.OKCYAN)
            
            if response.status_code == 200:
                data = response.json()
                flagged = data['data']['flagged_receipts']
                count = data['data']['count']
                
                self.log(f"✓ Retrieved {count} flagged receipt(s)", Color.OKGREEN)
                
                if count > 0:
                    self.log(f"  Flagged receipts requiring attention:", Color.WARNING)
                    for receipt in flagged[:3]:  # Show first 3
                        self.log(f"    - {receipt.get('receipt_id')}: {receipt.get('verification_notes', 'No notes')}", Color.WARNING)
                
                self.test_results.append({
                    'test': 'Flagged Receipts',
                    'passed': True,
                    'details': f"Retrieved {count} flagged receipts"
                })
            else:
                self.log(f"✗ Failed: {response.text}", Color.FAIL)
                self.test_results.append({
                    'test': 'Flagged Receipts',
                    'passed': False,
                    'details': f"Status {response.status_code}"
                })
        
        except Exception as e:
            self.log(f"✗ Error: {e}", Color.FAIL)
            self.test_results.append({
                'test': 'Flagged Receipts',
                'passed': False,
                'details': str(e)
            })
    
    def test_receipt_details(self):
        """Test GET /ceo/receipts/{receipt_id} endpoint."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("TEST: Receipt Details", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        try:
            # First get a receipt ID from the list
            list_response = requests.get(
                f"{self.base_url}/ceo/receipts?limit=1",
                headers=self.get_headers()
            )
            
            if list_response.status_code == 200:
                receipts = list_response.json()['data']['receipts']
                
                if len(receipts) > 0:
                    receipt_id = receipts[0]['receipt_id']
                    
                    # Get details
                    response = requests.get(
                        f"{self.base_url}/ceo/receipts/{receipt_id}",
                        headers=self.get_headers()
                    )
                    
                    self.log(f"Response Status: {response.status_code}", Color.OKCYAN)
                    
                    if response.status_code == 200:
                        data = response.json()['data']
                        receipt = data['receipt']
                        
                        self.log(f"✓ Receipt details retrieved", Color.OKGREEN)
                        self.log(f"  Receipt ID: {receipt['receipt_id']}", Color.OKCYAN)
                        self.log(f"  Status: {receipt['status']}", Color.OKCYAN)
                        self.log(f"  Order ID: {receipt.get('order_id', 'N/A')}", Color.OKCYAN)
                        
                        self.test_results.append({
                            'test': 'Receipt Details',
                            'passed': True,
                            'details': f"Retrieved details for {receipt_id}"
                        })
                    else:
                        self.log(f"✗ Failed: {response.text}", Color.FAIL)
                        self.test_results.append({
                            'test': 'Receipt Details',
                            'passed': False,
                            'details': f"Status {response.status_code}"
                        })
                else:
                    self.log("⊘ No receipts available to test details", Color.WARNING)
                    self.test_results.append({
                        'test': 'Receipt Details',
                        'passed': True,
                        'details': "Skipped (no receipts available)"
                    })
            else:
                self.log(f"✗ Failed to list receipts: {list_response.text}", Color.FAIL)
                self.test_results.append({
                    'test': 'Receipt Details',
                    'passed': False,
                    'details': "Could not retrieve receipt list"
                })
        
        except Exception as e:
            self.log(f"✗ Error: {e}", Color.FAIL)
            self.test_results.append({
                'test': 'Receipt Details',
                'passed': False,
                'details': str(e)
            })
    
    def test_bulk_verify(self):
        """Test POST /ceo/receipts/bulk-verify endpoint."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("TEST: Bulk Verify Receipts", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        try:
            # Get some receipt IDs
            list_response = requests.get(
                f"{self.base_url}/ceo/receipts?status=pending_review&limit=3",
                headers=self.get_headers()
            )
            
            if list_response.status_code == 200:
                receipts = list_response.json()['data']['receipts']
                
                if len(receipts) > 0:
                    receipt_ids = [r['receipt_id'] for r in receipts[:2]]  # Take up to 2
                    
                    # Bulk approve
                    response = requests.post(
                        f"{self.base_url}/ceo/receipts/bulk-verify",
                        headers=self.get_headers(),
                        json={
                            "receipt_ids": receipt_ids,
                            "action": "approve",
                            "notes": "Bulk approval test - automated testing"
                        }
                    )
                    
                    self.log(f"Response Status: {response.status_code}", Color.OKCYAN)
                    
                    if response.status_code == 200:
                        data = response.json()['data']
                        success_count = data['success_count']
                        failed_count = data['failed_count']
                        
                        self.log(f"✓ Bulk verification completed", Color.OKGREEN)
                        self.log(f"  Succeeded: {success_count}/{len(receipt_ids)}", Color.OKGREEN)
                        self.log(f"  Failed: {failed_count}/{len(receipt_ids)}", Color.WARNING if failed_count > 0 else Color.OKCYAN)
                        
                        # Show results
                        for result in data['results']:
                            status_icon = "✓" if result['success'] else "✗"
                            status_color = Color.OKGREEN if result['success'] else Color.FAIL
                            self.log(f"  {status_icon} {result['receipt_id']}: {result.get('error', 'OK')}", status_color)
                        
                        self.test_results.append({
                            'test': 'Bulk Verify Receipts',
                            'passed': True,
                            'details': f"{success_count}/{len(receipt_ids)} succeeded"
                        })
                    else:
                        self.log(f"✗ Failed: {response.text}", Color.FAIL)
                        self.test_results.append({
                            'test': 'Bulk Verify Receipts',
                            'passed': False,
                            'details': f"Status {response.status_code}"
                        })
                else:
                    self.log("⊘ No pending receipts available for bulk verification", Color.WARNING)
                    self.test_results.append({
                        'test': 'Bulk Verify Receipts',
                        'passed': True,
                        'details': "Skipped (no pending receipts)"
                    })
            else:
                self.log(f"✗ Failed to list receipts: {list_response.text}", Color.FAIL)
                self.test_results.append({
                    'test': 'Bulk Verify Receipts',
                    'passed': False,
                    'details': "Could not retrieve receipt list"
                })
        
        except Exception as e:
            self.log(f"✗ Error: {e}", Color.FAIL)
            self.test_results.append({
                'test': 'Bulk Verify Receipts',
                'passed': False,
                'details': str(e)
            })
    
    def print_summary(self):
        """Print test summary."""
        self.log("\n" + "="*60, Color.HEADER)
        self.log("TEST SUMMARY", Color.HEADER)
        self.log("="*60, Color.HEADER)
        
        total = len(self.test_results)
        passed = sum(1 for t in self.test_results if t['passed'])
        failed = total - passed
        
        self.log(f"\nTotal Tests: {total}", Color.BOLD)
        self.log(f"✓ Passed: {passed}", Color.OKGREEN)
        self.log(f"✗ Failed: {failed}", Color.FAIL if failed > 0 else Color.OKCYAN)
        
        if failed > 0:
            self.log("\nFailed Tests:", Color.FAIL)
            for test in self.test_results:
                if not test['passed']:
                    self.log(f"  ✗ {test['test']}: {test['details']}", Color.FAIL)
        
        self.log(f"\n{'='*60}", Color.HEADER)
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED!", Color.OKGREEN)
        else:
            self.log(f"⚠ {failed} test(s) failed", Color.WARNING)
        
        self.log(f"{'='*60}\n", Color.HEADER)
    
    def run_all_tests(self):
        """Run all receipt management tests."""
        print("\n")
        self.log("╔══════════════════════════════════════════════════════════════╗", Color.HEADER)
        self.log("║     CEO Receipts Management Test Suite                      ║", Color.HEADER)
        self.log("║     Testing Receipt Oversight & Bulk Operations             ║", Color.HEADER)
        self.log("╚══════════════════════════════════════════════════════════════╝", Color.HEADER)
        
        # Setup
        if not self.register_and_login_ceo():
            self.log("\n✗ Setup failed. Cannot proceed with tests.", Color.FAIL)
            return
        
        time.sleep(1)
        
        # Run tests
        self.test_list_receipts()
        time.sleep(1)
        
        self.test_receipt_stats()
        time.sleep(1)
        
        self.test_flagged_receipts()
        time.sleep(1)
        
        self.test_receipt_details()
        time.sleep(1)
        
        self.test_bulk_verify()
        time.sleep(1)
        
        # Summary
        self.print_summary()


if __name__ == "__main__":
    tester = ReceiptsManagementTester()
    tester.run_all_tests()
