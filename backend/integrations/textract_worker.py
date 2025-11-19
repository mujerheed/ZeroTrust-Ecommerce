"""
AWS Textract OCR Worker for Receipt Processing

This Lambda function is triggered by S3 events when receipts are uploaded.
It extracts text from receipts using AWS Textract and stores the results
with confidence scores.

Deployment:
- Deploy as separate Lambda function
- Trigger: S3 event (ObjectCreated) on TrustGuard-Receipts bucket
- IAM: Requires Textract:DetectDocumentText, DynamoDB:UpdateItem permissions
- Timeout: 60 seconds
- Memory: 512 MB

Flow:
1. S3 event → receipt uploaded
2. Lambda triggered with S3 key
3. Call Textract to analyze document
4. Extract: amount, bank name, date, account number
5. Calculate confidence score
6. Store in DynamoDB (TrustGuard-Receipts)
7. Optional: Flag low-confidence receipts for manual review
"""

import json
import boto3
import re
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

# Initialize AWS clients
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables (set in Lambda configuration)
import os
RECEIPTS_TABLE = os.environ.get('RECEIPTS_TABLE', 'TrustGuard-Receipts')
LOW_CONFIDENCE_THRESHOLD = float(os.environ.get('LOW_CONFIDENCE_THRESHOLD', '70.0'))

receipts_table = dynamodb.Table(RECEIPTS_TABLE)


class ReceiptOCRExtractor:
    """Extract structured data from receipt images using Textract."""
    
    # Nigerian bank patterns
    BANK_PATTERNS = [
        r'GTBank|Guaranty Trust Bank|GTB',
        r'First Bank|FBN|FirstBank',
        r'Access Bank|Access',
        r'Zenith Bank|Zenith',
        r'UBA|United Bank for Africa',
        r'Ecobank|ECO',
        r'Stanbic IBTC|Stanbic',
        r'Fidelity Bank|Fidelity',
        r'Union Bank|Union',
        r'Sterling Bank|Sterling',
        r'Wema Bank|WEMA',
        r'Polaris Bank|Polaris',
        r'Keystone Bank|Keystone',
        r'FCMB|First City Monument Bank',
        r'Heritage Bank|Heritage',
        r'Providus Bank|Providus'
    ]
    
    # Amount patterns (Naira)
    AMOUNT_PATTERNS = [
        r'(?:NGN|₦|N)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'Amount[:\s]*(?:NGN|₦|N)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'Total[:\s]*(?:NGN|₦|N)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})+\.\d{2})'  # Generic large number with decimals
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}'
    ]
    
    # Account number pattern
    ACCOUNT_PATTERNS = [
        r'Account[:\s]*(\d{10})',
        r'A/C[:\s]*(\d{10})',
        r'Acct[:\s]*(\d{10})',
        r'(\d{10})'  # Generic 10-digit number
    ]
    
    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key
        self.raw_text = ""
        self.blocks = []
        self.confidence_scores = []
    
    def analyze_document(self) -> Dict[str, Any]:
        """
        Call Textract to analyze receipt image.
        
        Returns:
            Dict with raw text, blocks, and confidence scores
        """
        try:
            response = textract.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': self.bucket,
                        'Name': self.key
                    }
                }
            )
            
            self.blocks = response.get('Blocks', [])
            
            # Extract text and confidence scores
            text_parts = []
            for block in self.blocks:
                if block['BlockType'] == 'LINE':
                    text_parts.append(block.get('Text', ''))
                    self.confidence_scores.append(block.get('Confidence', 0))
            
            self.raw_text = '\n'.join(text_parts)
            
            return {
                'raw_text': self.raw_text,
                'block_count': len(self.blocks),
                'avg_confidence': sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
            }
        
        except Exception as e:
            print(f"Textract analysis failed: {str(e)}")
            raise
    
    def extract_amount(self) -> Optional[Dict[str, Any]]:
        """Extract transaction amount from receipt text."""
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, self.raw_text, re.IGNORECASE)
            if matches:
                # Get largest amount (likely the total)
                amounts = []
                for match in matches:
                    # Clean amount string
                    clean_amount = match.replace(',', '').replace(' ', '')
                    try:
                        amounts.append(float(clean_amount))
                    except ValueError:
                        continue
                
                if amounts:
                    max_amount = max(amounts)
                    return {
                        'value': Decimal(str(max_amount)),
                        'currency': 'NGN',
                        'raw': match,
                        'confidence': self._get_confidence_for_text(match)
                    }
        
        return None
    
    def extract_bank(self) -> Optional[Dict[str, Any]]:
        """Extract bank name from receipt text."""
        for pattern in self.BANK_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                return {
                    'name': match.group(0),
                    'confidence': self._get_confidence_for_text(match.group(0))
                }
        
        return None
    
    def extract_date(self) -> Optional[Dict[str, Any]]:
        """Extract transaction date from receipt text."""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                return {
                    'raw': match.group(0),
                    'confidence': self._get_confidence_for_text(match.group(0))
                }
        
        return None
    
    def extract_account_number(self) -> Optional[Dict[str, Any]]:
        """Extract account number from receipt text."""
        for pattern in self.ACCOUNT_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                account = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if len(account) == 10:  # Nigerian accounts are 10 digits
                    return {
                        'value': account,
                        'confidence': self._get_confidence_for_text(account)
                    }
        
        return None
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all structured data from receipt."""
        # First analyze document
        analysis = self.analyze_document()
        
        # Extract individual fields
        amount = self.extract_amount()
        bank = self.extract_bank()
        date = self.extract_date()
        account = self.extract_account_number()
        
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
        
        overall_confidence = sum(field_confidences) / len(field_confidences) if field_confidences else analysis['avg_confidence']
        
        return {
            'raw_text': self.raw_text,
            'extracted_fields': {
                'amount': amount,
                'bank': bank,
                'date': date,
                'account_number': account
            },
            'metadata': {
                'block_count': analysis['block_count'],
                'textract_confidence': analysis['avg_confidence'],
                'extraction_confidence': overall_confidence,
                'extracted_at': datetime.utcnow().isoformat(),
                'fields_found': {
                    'amount': amount is not None,
                    'bank': bank is not None,
                    'date': date is not None,
                    'account': account is not None
                }
            }
        }
    
    def _get_confidence_for_text(self, text: str) -> float:
        """Get confidence score for specific text."""
        # Find blocks containing this text
        confidences = []
        for block in self.blocks:
            if block['BlockType'] == 'LINE' and text.lower() in block.get('Text', '').lower():
                confidences.append(block.get('Confidence', 0))
        
        return sum(confidences) / len(confidences) if confidences else 0


def update_receipt_with_ocr_data(receipt_id: str, ocr_data: Dict[str, Any]) -> bool:
    """
    Update receipt record in DynamoDB with Textract OCR data.
    
    Args:
        receipt_id: Receipt identifier (extracted from S3 key)
        ocr_data: Extracted OCR data
    
    Returns:
        True if updated successfully
    """
    try:
        # Prepare update
        extracted = ocr_data['extracted_fields']
        metadata = ocr_data['metadata']
        
        # Build update expression
        update_expr = 'SET textract_data = :data, ocr_confidence = :conf, ocr_processed_at = :ts'
        expr_values = {
            ':data': ocr_data,
            ':conf': Decimal(str(metadata['extraction_confidence'])),
            ':ts': metadata['extracted_at']
        }
        
        # Flag low-confidence extractions
        if metadata['extraction_confidence'] < LOW_CONFIDENCE_THRESHOLD:
            update_expr += ', ocr_low_confidence = :flag'
            expr_values[':flag'] = True
        
        # Update receipt
        receipts_table.update_item(
            Key={'receipt_id': receipt_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        print(f"Updated receipt {receipt_id} with OCR data (confidence: {metadata['extraction_confidence']:.2f}%)")
        return True
    
    except Exception as e:
        print(f"Failed to update receipt {receipt_id}: {str(e)}")
        return False


def extract_receipt_id_from_s3_key(s3_key: str) -> Optional[str]:
    """
    Extract receipt_id from S3 key.
    
    Expected format: receipts/{ceo_id}/{vendor_id}/{order_id}/{receipt_id}_{timestamp}.{ext}
    
    Args:
        s3_key: S3 object key
    
    Returns:
        receipt_id or None
    """
    try:
        # Get filename from path
        filename = s3_key.split('/')[-1]
        
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Extract receipt_id (before timestamp)
        receipt_id = name_without_ext.split('_')[0]
        
        return receipt_id
    
    except Exception as e:
        print(f"Failed to extract receipt_id from S3 key {s3_key}: {str(e)}")
        return None


def lambda_handler(event, context):
    """
    AWS Lambda handler for Textract OCR processing.
    
    Triggered by S3 event when receipt is uploaded.
    
    Args:
        event: S3 event notification
        context: Lambda context
    
    Returns:
        Response dict with status and results
    """
    print(f"Textract worker triggered: {json.dumps(event)}")
    
    try:
        # Parse S3 event
        for record in event.get('Records', []):
            # Get S3 details
            s3_info = record.get('s3', {})
            bucket = s3_info.get('bucket', {}).get('name')
            key = s3_info.get('object', {}).get('key')
            
            if not bucket or not key:
                print(f"Invalid S3 event: {record}")
                continue
            
            print(f"Processing receipt: s3://{bucket}/{key}")
            
            # Extract receipt_id from S3 key
            receipt_id = extract_receipt_id_from_s3_key(key)
            if not receipt_id:
                print(f"Could not extract receipt_id from key: {key}")
                continue
            
            # Analyze receipt with Textract
            extractor = ReceiptOCRExtractor(bucket, key)
            ocr_data = extractor.extract_all()
            
            print(f"OCR extraction complete:")
            print(f"  - Confidence: {ocr_data['metadata']['extraction_confidence']:.2f}%")
            print(f"  - Amount: {ocr_data['extracted_fields']['amount']}")
            print(f"  - Bank: {ocr_data['extracted_fields']['bank']}")
            print(f"  - Date: {ocr_data['extracted_fields']['date']}")
            
            # Update DynamoDB with OCR results
            success = update_receipt_with_ocr_data(receipt_id, ocr_data)
            
            if success:
                print(f"Successfully processed receipt {receipt_id}")
            else:
                print(f"Failed to update receipt {receipt_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'OCR processing complete',
                'receipts_processed': len(event.get('Records', []))
            })
        }
    
    except Exception as e:
        print(f"Textract worker error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    # Mock S3 event
    test_event = {
        'Records': [
            {
                's3': {
                    'bucket': {
                        'name': 'trustguard-receipts'
                    },
                    'object': {
                        'key': 'receipts/ceo_001/vendor_001/order_123/receipt_abc123_20251119_140000.jpg'
                    }
                }
            }
        ]
    }
    
    result = lambda_handler(test_event, None)
    print(f"Result: {json.dumps(result, indent=2)}")
