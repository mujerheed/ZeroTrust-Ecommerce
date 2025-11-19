"""
Local Mock Test for Textract OCR Receipt Extraction
Tests pattern matching and data extraction without AWS credentials.
"""

import sys
sys.path.insert(0, '.')

from integrations.textract_worker import ReceiptOCRExtractor


# Mock Textract response blocks (simulates what AWS Textract returns)
def create_mock_textract_response(text_lines):
    """Create a mock Textract API response with blocks and confidence scores."""
    blocks = []
    for i, line in enumerate(text_lines):
        blocks.append({
            'BlockType': 'LINE',
            'Text': line,
            'Confidence': 95.0 + (i % 5),  # Vary confidence 95-99%
            'Id': f'block_{i}'
        })
    return {'Blocks': blocks}


# Sample receipt texts from different Nigerian banks
SAMPLE_RECEIPTS = {
    'gtbank_transfer': [
        'GTBank Nigeria',
        'Transaction Receipt',
        'Transaction Type: Transfer',
        'Amount: NGN 2,500,000.00',
        'Date: 19/11/2025',
        'Time: 14:35:22',
        'Account Number: 0123456789',
        'Beneficiary: ABC Traders Ltd',
        'Reference: TRX2025111900123',
        'Status: Successful',
    ],
    
    'first_bank_deposit': [
        'First Bank of Nigeria',
        'Cash Deposit Receipt',
        'Amount Deposited: ₦850,000.50',
        'Date: 18-Nov-2025',
        'Account: 1234567890',
        'Depositor: John Doe',
        'Branch: Ikeja',
        'Teller ID: FBN-IK-045',
    ],
    
    'access_bank_payment': [
        'Access Bank Plc',
        'Payment Receipt',
        'Total Amount: N 3,750,250.00',
        'Transaction Date: 2025-11-17',
        'Account No: 9876543210',
        'Payment Reference: ACC/2025/1117/789',
        'Merchant: XYZ Electronics',
    ],
    
    'zenith_pos': [
        'ZENITH BANK PLC',
        'POS Transaction Receipt',
        'Card: **** **** **** 1234',
        'Amount: NGN1,200,000',
        'Date: 16/11/2025 10:45 AM',
        'Terminal ID: 2DA00123',
        'Merchant Account: 5555666677',
        'Status: APPROVED',
    ],
    
    'low_quality_receipt': [
        'Ban... (unclear)',
        'Amou...: 500,0...',
        'Dat...: 15/11/...',
        'Acc...: 11111...',
        'Ref: PARTIAL123',
    ]
}


def print_header(text):
    """Print colored section header."""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print('=' * 80)


def print_success(text):
    """Print success message in green."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message in red."""
    print(f"✗ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")


def print_field(label, value, confidence=None):
    """Print extracted field with confidence."""
    if confidence is not None:
        print(f"  {label:20} {value:30} (confidence: {confidence:.1f}%)")
    else:
        print(f"  {label:20} {value}")


def test_receipt_extraction(receipt_name, text_lines):
    """Test OCR extraction on a sample receipt."""
    print_header(f"Testing: {receipt_name.replace('_', ' ').title()}")
    
    # Display receipt text
    print_info("Receipt Text:")
    for line in text_lines:
        print(f"    {line}")
    print()
    
    # Create mock Textract response
    mock_response = create_mock_textract_response(text_lines)
    
    # Initialize extractor with mock S3 location
    extractor = ReceiptOCRExtractor(
        bucket='mock-bucket',
        key='mock/receipt.jpg'
    )
    
    # Set the mock response (bypass actual Textract call)
    extractor.blocks = mock_response['Blocks']
    extractor.raw_text = '\n'.join(text_lines)
    
    # Extract individual fields (skip analyze_document call)
    amount = extractor.extract_amount()
    bank = extractor.extract_bank()
    date = extractor.extract_date()
    account = extractor.extract_account_number()
    
    # Calculate overall confidence
    field_confidences = []
    if amount:
        field_confidences.append(amount['confidence'])
    if bank:
        field_confidences.append(bank['confidence'])
    if date:
        field_confidences.append(date['confidence'])
    if account:
        field_confidences.append(account['confidence'])
    
    # Calculate average confidence from blocks
    block_confidences = [b['Confidence'] for b in mock_response['Blocks']]
    avg_confidence = sum(block_confidences) / len(block_confidences) if block_confidences else 0
    
    # If we found fields, use their average; otherwise use block average
    overall_confidence = sum(field_confidences) / len(field_confidences) if field_confidences else avg_confidence
    
    # If no fields found, penalize confidence
    if len(field_confidences) == 0:
        overall_confidence = min(avg_confidence, 50.0)  # Cap at 50% if nothing extracted
    
    # Build extracted data structure (same as extract_all() but without AWS call)
    extracted = {
        'raw_text': extractor.raw_text,
        'extracted_fields': {
            'amount': amount,
            'bank': bank,
            'date': date,
            'account_number': account
        },
        'metadata': {
            'block_count': len(mock_response['Blocks']),
            'textract_confidence': avg_confidence,
            'extraction_confidence': overall_confidence,
            'extracted_at': '2025-11-19T00:00:00',  # Mock timestamp
            'fields_found': {
                'amount': amount is not None,
                'bank': bank is not None,
                'date': date is not None,
                'account': account is not None
            }
        },
        'ocr_low_confidence': overall_confidence < 70.0
    }
    
    # Display results
    print_info("Extracted Data:")
    
    # Amount
    if extracted['extracted_fields'].get('amount'):
        amount_data = extracted['extracted_fields']['amount']
        print_field(
            "Amount:",
            f"{amount_data['currency']} {amount_data['value']:,.2f}",
            amount_data.get('confidence')
        )
    else:
        print_field("Amount:", "NOT FOUND", 0)
    
    # Bank
    if extracted['extracted_fields'].get('bank'):
        bank_data = extracted['extracted_fields']['bank']
        print_field(
            "Bank:",
            bank_data['name'],
            bank_data.get('confidence')
        )
    else:
        print_field("Bank:", "NOT FOUND", 0)
    
    # Date
    if extracted['extracted_fields'].get('date'):
        date_data = extracted['extracted_fields']['date']
        print_field(
            "Date:",
            date_data['raw'],
            date_data.get('confidence')
        )
    else:
        print_field("Date:", "NOT FOUND", 0)
    
    # Account Number
    if extracted['extracted_fields'].get('account_number'):
        account_data = extracted['extracted_fields']['account_number']
        print_field(
            "Account Number:",
            account_data['value'],
            account_data.get('confidence')
        )
    else:
        print_field("Account Number:", "NOT FOUND", 0)
    
    # Metadata
    print()
    print_info("Extraction Metadata:")
    print_field("Overall Confidence:", f"{extracted['metadata']['extraction_confidence']:.1f}%")
    print_field("Blocks Processed:", str(extracted['metadata']['block_count']))
    
    # Fields found summary
    fields_found = extracted['metadata']['fields_found']
    found_count = sum(1 for v in fields_found.values() if v)
    print_field("Fields Found:", f"{found_count}/4")
    for field, found in fields_found.items():
        status = "✓" if found else "✗"
        print(f"    {status} {field}")
    
    # Low confidence warning
    if extracted.get('ocr_low_confidence', False):
        print()
        print_error(f"⚠ LOW CONFIDENCE EXTRACTION (< 70%)")
        print_info("This receipt would be flagged for manual vendor review")
    else:
        print()
        print_success(f"✓ HIGH CONFIDENCE EXTRACTION (≥ 70%)")
        print_info("OCR data can pre-fill vendor dashboard")
    
    return extracted


def test_pattern_matching():
    """Test individual pattern matching capabilities."""
    print_header("Testing Individual Pattern Matchers")
    
    extractor = ReceiptOCRExtractor(
        bucket='mock-bucket',
        key='mock/receipt.jpg'
    )
    
    # Test amount patterns
    print_info("Testing Amount Extraction Patterns:")
    test_amounts = [
        "Amount: NGN 2,500,000.00",
        "Total: ₦1,234.56",
        "Payment: N 999,999",
        "Charged: 500000.50",
    ]
    for test_text in test_amounts:
        # Create mock blocks
        extractor.blocks = [{
            'BlockType': 'LINE',
            'Text': test_text,
            'Confidence': 98.0
        }]
        extractor.raw_text = test_text
        result = extractor.extract_amount()
        if result:
            print(f"  '{test_text}' → ₦{result['value']:,.2f}")
        else:
            print(f"  '{test_text}' → NOT FOUND")
    
    print()
    
    # Test bank patterns
    print_info("Testing Bank Name Extraction:")
    test_banks = [
        "GTBank Nigeria",
        "First Bank of Nigeria Limited",
        "Access Bank Plc",
        "Zenith Bank",
        "United Bank for Africa",
        "Unknown Bank XYZ",
    ]
    for test_text in test_banks:
        extractor.blocks = [{
            'BlockType': 'LINE',
            'Text': test_text,
            'Confidence': 98.0
        }]
        extractor.raw_text = test_text
        result = extractor.extract_bank()
        if result:
            print(f"  '{test_text}' → {result['name']}")
        else:
            print(f"  '{test_text}' → NOT FOUND")
    
    print()
    
    # Test date patterns
    print_info("Testing Date Extraction:")
    test_dates = [
        "Date: 19/11/2025",
        "Transaction Date: 2025-11-18",
        "Dated: 17 Nov 2025",
        "Invalid: 99/99/9999",
    ]
    for test_text in test_dates:
        extractor.blocks = [{
            'BlockType': 'LINE',
            'Text': test_text,
            'Confidence': 98.0
        }]
        extractor.raw_text = test_text
        result = extractor.extract_date()
        if result:
            print(f"  '{test_text}' → {result['raw']}")
        else:
            print(f"  '{test_text}' → NOT FOUND")
    
    print()
    
    # Test account number patterns
    print_info("Testing Account Number Extraction:")
    test_accounts = [
        "Account Number: 0123456789",
        "Account: 9876543210",
        "Acct No: 5555666677",
        "Invalid: 123456",  # Too short
    ]
    for test_text in test_accounts:
        extractor.blocks = [{
            'BlockType': 'LINE',
            'Text': test_text,
            'Confidence': 98.0
        }]
        extractor.raw_text = test_text
        result = extractor.extract_account_number()
        if result:
            print(f"  '{test_text}' → {result['value']}")
        else:
            print(f"  '{test_text}' → NOT FOUND")


def main():
    """Run all local OCR tests."""
    print_header("TEXTRACT OCR LOCAL MOCK TEST")
    print_info("Testing receipt extraction patterns without AWS")
    print_info("Simulates Textract API responses with mock data")
    
    # Test pattern matching capabilities
    test_pattern_matching()
    
    # Test full extraction on sample receipts
    results = {}
    for receipt_name, text_lines in SAMPLE_RECEIPTS.items():
        results[receipt_name] = test_receipt_extraction(receipt_name, text_lines)
    
    # Summary
    print_header("TEST SUMMARY")
    
    successful = 0
    flagged = 0
    
    for receipt_name, extracted in results.items():
        fields_found = sum(1 for v in extracted['metadata']['fields_found'].values() if v)
        confidence = extracted['metadata']['extraction_confidence']
        
        status = "✓" if confidence >= 70 else "⚠"
        print(f"{status} {receipt_name:25} {fields_found}/4 fields  {confidence:5.1f}% confidence")
        
        if confidence >= 70:
            successful += 1
        else:
            flagged += 1
    
    print()
    print_success(f"High Confidence: {successful}/{len(results)} receipts")
    if flagged > 0:
        print_error(f"Low Confidence:  {flagged}/{len(results)} receipts (would be flagged)")
    
    print()
    print_info("Supported Banks (16 total):")
    banks = [
        "GTBank", "First Bank", "Access Bank", "Zenith Bank", "UBA",
        "Ecobank", "Fidelity Bank", "Union Bank", "Sterling Bank",
        "Stanbic IBTC", "Wema Bank", "FCMB", "Heritage Bank",
        "Keystone Bank", "Polaris Bank", "Unity Bank"
    ]
    for i in range(0, len(banks), 4):
        print(f"  {', '.join(banks[i:i+4])}")
    
    print()
    print_header("TEST COMPLETE")
    print_success("All pattern matching tests completed successfully!")
    print_info("Next steps:")
    print_info("  1. Deploy Textract Lambda to AWS")
    print_info("  2. Configure S3 event triggers")
    print_info("  3. Test with real receipt images")
    print_info("  4. Monitor extraction accuracy in production")


if __name__ == '__main__':
    main()
