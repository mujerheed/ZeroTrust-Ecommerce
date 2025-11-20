"""
Dedicated OCR Auto-Approval Workflow Test
Tests the complete flow: Receipt Upload → Textract OCR → Auto-Validation → Approval/Flag/Escalate

Usage:
    python test_ocr_workflow.py
    
Requirements:
    pip install requests boto3 python-dotenv pillow
"""

import os
import requests
import boto3
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
RECEIPT_BUCKET = os.getenv("RECEIPT_BUCKET", "trustguard-receipts-605009361024-dev")

# Test credentials
TEST_VENDOR_PHONE = os.getenv("TEST_VENDOR_PHONE", "+2348087654321")
TEST_BUYER_ID = os.getenv("TEST_BUYER_ID", "wa_test_buyer_1234")
TEST_CEO_ID = os.getenv("TEST_CEO_ID", "ceo_test_001")


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(step_num: int, text: str):
    """Print workflow step"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}[Step {step_num}] {text}{Colors.ENDC}")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def generate_mock_receipt_image(amount: float, bank_name: str = "GTBank") -> bytes:
    """Generate a mock bank receipt image with text"""
    # Create image
    width, height = 800, 1200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if unavailable
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw header
    draw.rectangle([(0, 0), (width, 150)], fill='#00008B')
    draw.text((width//2, 75), bank_name, fill='white', font=font_large, anchor="mm")
    
    # Draw receipt content
    y_offset = 200
    
    # Transaction details
    details = [
        ("TRANSACTION RECEIPT", font_large, 'black'),
        ("", font_small, 'black'),
        (f"Date: {datetime.now().strftime('%d %b %Y')}", font_medium, 'black'),
        (f"Time: {datetime.now().strftime('%H:%M:%S')}", font_medium, 'black'),
        ("", font_small, 'black'),
        ("CREDIT TRANSACTION", font_medium, 'green'),
        ("", font_small, 'black'),
        (f"Amount: ₦{amount:,.2f}", font_large, 'green'),
        ("", font_small, 'black'),
        ("Transaction Successful", font_medium, 'green'),
        ("", font_small, 'black'),
        (f"Reference: TXN{int(time.time())}", font_small, 'black'),
        (f"Session ID: {int(time.time() * 1000)}", font_small, 'black'),
    ]
    
    for text, font, color in details:
        draw.text((width//2, y_offset), text, fill=color, font=font, anchor="mm")
        y_offset += 60
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()


def create_test_order(vendor_token: str, amount: float) -> Optional[str]:
    """Create a test order"""
    print_step(1, "Creating test order")
    
    order_data = {
        "buyer_id": TEST_BUYER_ID,
        "amount": amount,
        "description": f"OCR Test Order - Amount: ₦{amount:,.2f}",
        "product_name": "Test Product"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/vendor/orders",
        headers={
            "Authorization": f"Bearer {vendor_token}",
            "Content-Type": "application/json"
        },
        json=order_data,
        timeout=30
    )
    
    if response.status_code == 201:
        order_id = response.json().get("data", {}).get("order_id")
        print_success(f"Order created: {order_id}")
        print_info(f"Amount: ₦{amount:,.2f}")
        return order_id
    else:
        print_error(f"Failed to create order: {response.text}")
        return None


def upload_receipt_to_s3(order_id: str, receipt_image: bytes, vendor_id: str) -> bool:
    """Upload mock receipt to S3"""
    print_step(2, "Uploading receipt to S3")
    
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    # S3 key format: receipts/{ceo_id}/{vendor_id}/{order_id}/receipt.png
    s3_key = f"receipts/{TEST_CEO_ID}/{vendor_id}/{order_id}/receipt_{int(time.time())}.png"
    
    try:
        s3_client.put_object(
            Bucket=RECEIPT_BUCKET,
            Key=s3_key,
            Body=receipt_image,
            ContentType='image/png',
            Metadata={
                'order_id': order_id,
                'vendor_id': vendor_id,
                'upload_timestamp': str(int(time.time()))
            }
        )
        print_success(f"Receipt uploaded to S3: {s3_key}")
        return True
    except Exception as e:
        print_error(f"Failed to upload receipt: {e}")
        return False


def trigger_textract_ocr(order_id: str, s3_key: str) -> bool:
    """Trigger Textract OCR processing"""
    print_step(3, "Triggering Textract OCR processing")
    
    # In production, this would be triggered by S3 event → Lambda
    # For testing, we'll simulate the Textract worker
    
    textract_client = boto3.client('textract', region_name=AWS_REGION)
    
    try:
        # Start document text detection
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': RECEIPT_BUCKET,
                    'Name': s3_key
                }
            }
        )
        
        # Extract text blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
        
        print_success("Textract OCR completed")
        print_info(f"Extracted {len(text_blocks)} text blocks")
        
        # Print extracted text
        print("\nExtracted text:")
        for i, text in enumerate(text_blocks[:10], 1):
            print(f"  {i}. {text}")
        
        return True
    except Exception as e:
        print_error(f"Textract OCR failed: {e}")
        return False


def check_auto_approval_result(vendor_token: str, order_id: str, expected_status: str) -> bool:
    """Check if auto-approval logic executed correctly"""
    print_step(4, "Checking auto-approval result")
    
    # Wait a bit for processing
    print_info("Waiting for auto-approval processing (10 seconds)...")
    time.sleep(10)
    
    # Get order details
    response = requests.get(
        f"{API_BASE_URL}/vendor/orders/{order_id}",
        headers={"Authorization": f"Bearer {vendor_token}"},
        timeout=30
    )
    
    if response.status_code == 200:
        order = response.json().get("data", {})
        status = order.get("status")
        ocr_confidence = order.get("receipt_ocr_confidence")
        ocr_amount = order.get("receipt_ocr_amount")
        
        print_success(f"Order status: {status}")
        print_info(f"OCR Confidence: {ocr_confidence}%")
        print_info(f"OCR Amount: ₦{ocr_amount}")
        
        # Verify expected status
        if status == expected_status:
            print_success(f"✓ Auto-approval logic worked correctly: {status}")
            return True
        else:
            print_error(f"✗ Expected status '{expected_status}', got '{status}'")
            return False
    else:
        print_error(f"Failed to fetch order: {response.text}")
        return False


def test_scenario_1_low_amount_auto_approve(vendor_token: str, vendor_id: str):
    """Test Scenario 1: Low amount (< ₦1M) with valid OCR → Should auto-approve"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}SCENARIO 1: Low Amount Auto-Approve (OCR Valid){Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    
    amount = 50000.0  # ₦50,000
    
    # Create order
    order_id = create_test_order(vendor_token, amount)
    if not order_id:
        return False
    
    # Generate receipt with matching amount
    receipt_image = generate_mock_receipt_image(amount)
    
    # Upload to S3
    s3_key = f"receipts/{TEST_CEO_ID}/{vendor_id}/{order_id}/receipt_{int(time.time())}.png"
    if not upload_receipt_to_s3(order_id, receipt_image, vendor_id):
        return False
    
    # Trigger OCR
    if not trigger_textract_ocr(order_id, s3_key):
        return False
    
    # Check result (should auto-approve)
    return check_auto_approval_result(vendor_token, order_id, "approved")


def test_scenario_2_high_amount_escalate(vendor_token: str, vendor_id: str):
    """Test Scenario 2: High amount (≥ ₦1M) → Should escalate to CEO"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}SCENARIO 2: High Amount Escalation (≥ ₦1M){Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    
    amount = 1500000.0  # ₦1.5M
    
    # Create order
    order_id = create_test_order(vendor_token, amount)
    if not order_id:
        return False
    
    # Generate receipt
    receipt_image = generate_mock_receipt_image(amount)
    
    # Upload to S3
    s3_key = f"receipts/{TEST_CEO_ID}/{vendor_id}/{order_id}/receipt_{int(time.time())}.png"
    if not upload_receipt_to_s3(order_id, receipt_image, vendor_id):
        return False
    
    # Trigger OCR
    if not trigger_textract_ocr(order_id, s3_key):
        return False
    
    # Check result (should escalate to CEO)
    return check_auto_approval_result(vendor_token, order_id, "pending_ceo")


def test_scenario_3_ocr_mismatch_flag(vendor_token: str, vendor_id: str):
    """Test Scenario 3: OCR amount mismatch → Should flag for manual review"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}SCENARIO 3: OCR Mismatch (Flag for Manual Review){Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    
    order_amount = 75000.0  # ₦75,000
    receipt_amount = 50000.0  # ₦50,000 (mismatch!)
    
    # Create order with one amount
    order_id = create_test_order(vendor_token, order_amount)
    if not order_id:
        return False
    
    # Generate receipt with different amount
    receipt_image = generate_mock_receipt_image(receipt_amount)
    
    # Upload to S3
    s3_key = f"receipts/{TEST_CEO_ID}/{vendor_id}/{order_id}/receipt_{int(time.time())}.png"
    if not upload_receipt_to_s3(order_id, receipt_image, vendor_id):
        return False
    
    # Trigger OCR
    if not trigger_textract_ocr(order_id, s3_key):
        return False
    
    # Check result (should flag)
    return check_auto_approval_result(vendor_token, order_id, "flagged")


def main():
    """Run OCR workflow tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║         TrustGuard OCR Auto-Approval Workflow Test Suite                  ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print_info("This test suite validates the complete OCR auto-approval workflow:")
    print_info("  1. Receipt Upload → S3")
    print_info("  2. Textract OCR Processing")
    print_info("  3. Auto-Validation (amount match, confidence)")
    print_info("  4. Decision: Auto-Approve / Flag / Escalate")
    
    # Get vendor authentication
    print_warning(f"\nAuthentication required for vendor: {TEST_VENDOR_PHONE}")
    vendor_otp = input(f"{Colors.OKCYAN}Enter Vendor OTP (8 chars): {Colors.ENDC}").strip()
    
    response = requests.post(
        f"{API_BASE_URL}/auth/vendor/verify-otp",
        json={"phone_number": TEST_VENDOR_PHONE, "otp": vendor_otp},
        timeout=30
    )
    
    if response.status_code != 200:
        print_error("Vendor authentication failed")
        return
    
    vendor_token = response.json().get("data", {}).get("token")
    vendor_id = response.json().get("data", {}).get("user", {}).get("vendor_id")
    
    print_success("Vendor authenticated successfully")
    
    # Run test scenarios
    scenarios = [
        ("Scenario 1: Low Amount Auto-Approve", test_scenario_1_low_amount_auto_approve),
        ("Scenario 2: High Amount Escalation", test_scenario_2_high_amount_escalate),
        ("Scenario 3: OCR Mismatch Flag", test_scenario_3_ocr_mismatch_flag),
    ]
    
    results = {}
    
    for scenario_name, scenario_func in scenarios:
        try:
            success = scenario_func(vendor_token, vendor_id)
            results[scenario_name] = "PASS" if success else "FAIL"
        except Exception as e:
            print_error(f"Scenario '{scenario_name}' raised exception: {e}")
            results[scenario_name] = "ERROR"
    
    # Print summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    for scenario, result in results.items():
        if result == "PASS":
            print_success(f"{scenario}: {result}")
        else:
            print_error(f"{scenario}: {result}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r == "PASS")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} scenarios passed{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
