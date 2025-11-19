# Textract OCR Integration - Deployment Guide

## Overview

The Textract OCR worker automatically extracts structured data from uploaded receipts:
- **Amount**: Transaction amount in Naira (₦)
- **Bank**: Bank name (supports all major Nigerian banks)
- **Date**: Transaction date
- **Account Number**: 10-digit account number
- **Confidence Score**: Overall extraction quality (0-100%)

---

## Architecture

```
Buyer uploads receipt
       ↓
S3 (TrustGuard-Receipts bucket)
       ↓
S3 Event Notification
       ↓
Lambda (Textract Worker)
       ↓
AWS Textract API
       ↓
Extract structured data
       ↓
Update DynamoDB (TrustGuard-Receipts)
       ↓
Optional: Flag low-confidence for manual review
```

---

## Deployment Steps

### 1. Create Lambda Function

```bash
cd backend/integrations
zip -r textract_worker.zip textract_worker.py

aws lambda create-function \
  --function-name TrustGuard-TextractWorker \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/TrustGuard-TextractLambdaRole \
  --handler textract_worker.lambda_handler \
  --zip-file fileb://textract_worker.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{RECEIPTS_TABLE=TrustGuard-Receipts,LOW_CONFIDENCE_THRESHOLD=70.0}"
```

### 2. Create IAM Role

Create `TrustGuard-TextractLambdaRole` with this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::trustguard-receipts/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/TrustGuard-Receipts"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 3. Configure S3 Event Notification

```bash
aws s3api put-bucket-notification-configuration \
  --bucket trustguard-receipts \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "Id": "TextractOCRTrigger",
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:TrustGuard-TextractWorker",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {
                "Name": "prefix",
                "Value": "receipts/"
              },
              {
                "Name": "suffix",
                "Value": ".jpg"
              }
            ]
          }
        }
      }
    ]
  }'
```

**Note**: Add separate configurations for `.png`, `.jpeg`, `.pdf` suffixes.

### 4. Grant S3 Permission to Invoke Lambda

```bash
aws lambda add-permission \
  --function-name TrustGuard-TextractWorker \
  --principal s3.amazonaws.com \
  --statement-id S3InvokeLambda \
  --action "lambda:InvokeFunction" \
  --source-arn arn:aws:s3:::trustguard-receipts \
  --source-account YOUR_ACCOUNT_ID
```

---

## Extracted Data Schema

The Textract worker updates the receipt record with this structure:

```python
{
  "receipt_id": "receipt_abc123",
  "textract_data": {
    "raw_text": "Full extracted text from receipt...",
    "extracted_fields": {
      "amount": {
        "value": 2500000,  # Decimal
        "currency": "NGN",
        "raw": "₦2,500,000.00",
        "confidence": 95.2
      },
      "bank": {
        "name": "GTBank",
        "confidence": 98.7
      },
      "date": {
        "raw": "19/11/2025",
        "confidence": 92.3
      },
      "account_number": {
        "value": "0123456789",
        "confidence": 97.1
      }
    },
    "metadata": {
      "block_count": 45,
      "textract_confidence": 94.5,
      "extraction_confidence": 95.8,
      "extracted_at": "2025-11-19T14:30:22.123456",
      "fields_found": {
        "amount": true,
        "bank": true,
        "date": true,
        "account": true
      }
    }
  },
  "ocr_confidence": 95.8,  # Decimal - for quick filtering
  "ocr_processed_at": "2025-11-19T14:30:22.123456",
  "ocr_low_confidence": false  # true if < 70%
}
```

---

## Supported Banks (Pattern Matching)

The OCR worker recognizes these Nigerian banks:
- GTBank / Guaranty Trust Bank
- First Bank / FBN / FirstBank
- Access Bank
- Zenith Bank
- UBA / United Bank for Africa
- Ecobank
- Stanbic IBTC
- Fidelity Bank
- Union Bank
- Sterling Bank
- Wema Bank
- Polaris Bank
- Keystone Bank
- FCMB / First City Monument Bank
- Heritage Bank
- Providus Bank

---

## Low-Confidence Handling

If extraction confidence < 70%:
1. `ocr_low_confidence` flag set to `true`
2. Vendor dashboard shows "OCR Low Confidence" warning
3. Vendor should manually verify receipt details
4. Optional: Auto-escalate low-confidence receipts to CEO

---

## Testing Locally

```bash
cd backend/integrations

# Install dependencies
pip install boto3

# Set environment variables
export AWS_REGION=us-east-1
export RECEIPTS_TABLE=TrustGuard-Receipts
export LOW_CONFIDENCE_THRESHOLD=70.0

# Run test
python textract_worker.py
```

---

## Monitoring

### CloudWatch Metrics
- Lambda invocations
- Duration (should be < 10 seconds)
- Errors (check logs for Textract API failures)

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/TrustGuard-TextractWorker --follow
```

### DynamoDB Queries
```bash
# Count receipts with OCR data
aws dynamodb scan \
  --table-name TrustGuard-Receipts \
  --filter-expression "attribute_exists(ocr_confidence)"

# Find low-confidence receipts
aws dynamodb scan \
  --table-name TrustGuard-Receipts \
  --filter-expression "ocr_low_confidence = :flag" \
  --expression-attribute-values '{":flag":{"BOOL":true}}'
```

---

## Cost Estimation

### AWS Textract Pricing (us-east-1)
- **DetectDocumentText**: $0.0015 per page
- Expected: 1 page per receipt
- Example: 10,000 receipts/month = $15/month

### Lambda Pricing
- **Compute**: $0.0000166667 per GB-second
- 512 MB, 5 seconds average = $0.000041 per execution
- Example: 10,000 receipts/month = $0.41/month

### Total: ~$15.50/month for 10,000 receipts

---

## Troubleshooting

### Issue: Lambda not triggered
- Check S3 event notification configuration
- Verify Lambda has S3 invoke permission
- Check CloudWatch logs for errors

### Issue: Textract API errors
- Verify IAM role has `textract:DetectDocumentText` permission
- Check image format (JPEG, PNG, PDF only)
- Verify image is < 5MB

### Issue: Low extraction confidence
- Check image quality (blurry, rotated, poor lighting)
- Verify receipt is from supported bank
- Try different Textract API (AnalyzeDocument vs DetectDocumentText)

---

## Future Enhancements

1. **Textract Queries** - Use `AnalyzeDocument` with queries for better accuracy
2. **Custom ML Model** - Train custom model for Nigerian receipts
3. **Multi-page Support** - Handle PDF receipts with multiple pages
4. **Auto-rotation** - Detect and correct rotated images
5. **Fraud Detection** - ML model to detect forged receipts

---

## Integration with Vendor Workflow

When vendor reviews receipt:
1. Vendor sees OCR-extracted data pre-filled
2. If OCR confidence > 90%: Auto-suggest "Approve"
3. If OCR confidence < 70%: Show warning "Manual verification required"
4. Vendor can override OCR data if incorrect
5. Final verification status saved regardless of OCR

---

## Deployment Checklist

- [ ] Deploy Lambda function with correct IAM role
- [ ] Configure S3 event notifications (jpg, png, pdf)
- [ ] Grant S3 permission to invoke Lambda
- [ ] Test with sample receipt upload
- [ ] Monitor CloudWatch logs for errors
- [ ] Verify DynamoDB updates with OCR data
- [ ] Update vendor dashboard to show OCR results
- [ ] Document low-confidence escalation workflow
