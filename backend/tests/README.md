# TrustGuard Phase 2 Test Suite

Comprehensive testing scripts for Phase 2 backend features: OCR Auto-Approval, Vendor Preferences, CEO Chatbot Config, Analytics, and Notifications.

## 📋 Test Scripts

### 1. `test_phase2_endpoints.py`
Tests all Phase 2 API endpoints against deployed infrastructure.

**What it tests:**
- ✅ CEO chatbot configuration (`GET/PUT /ceo/chatbot/settings`)
- ✅ Vendor preferences (`GET/PUT /vendor/preferences`)
- ✅ Vendor risk scores (`GET /ceo/vendors` with `risk_score` field)
- ✅ Analytics endpoints (`/vendor/analytics/orders-by-day`, `/ceo/analytics/fraud-trends`)
- ✅ Notification polling (`GET /vendor/notifications/unread`)
- ✅ OCR auto-approval workflow verification

**Usage:**
```bash
cd backend/tests
python test_phase2_endpoints.py
```

**Requirements:**
```bash
pip install requests pytest python-dotenv
```

---

### 2. `test_ocr_workflow.py`
Dedicated OCR auto-approval workflow testing with synthetic receipts.

**What it tests:**
- ✅ **Scenario 1**: Low amount (< ₦1M) with valid OCR → **Auto-approve**
- ✅ **Scenario 2**: High amount (≥ ₦1M) → **Escalate to CEO**
- ✅ **Scenario 3**: OCR amount mismatch → **Flag for manual review**

**Workflow:**
1. Creates test order with specific amount
2. Generates mock bank receipt image
3. Uploads receipt to S3
4. Triggers Textract OCR processing
5. Validates auto-approval decision

**Usage:**
```bash
cd backend/tests
python test_ocr_workflow.py
```

**Requirements:**
```bash
pip install requests boto3 python-dotenv pillow
```

**⚠️ Note:** Requires AWS credentials with permissions for:
- S3 (PutObject to `trustguard-receipts-*` bucket)
- Textract (DetectDocumentText)
- DynamoDB (read/write to TrustGuard tables)

---

## 🔧 Setup

### 1. Install Dependencies

```bash
cd backend/tests
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests boto3 python-dotenv pillow pytest
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and set your values:
```env
API_BASE_URL=https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod
AWS_REGION=us-east-1
RECEIPT_BUCKET=trustguard-receipts-605009361024-dev

TEST_CEO_PHONE=+2348012345678
TEST_VENDOR_PHONE=+2348087654321
TEST_BUYER_ID=wa_test_buyer_1234
TEST_CEO_ID=ceo_test_001
```

### 3. AWS Credentials (for OCR tests)

Ensure AWS CLI is configured:
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

---

## 🚀 Running Tests

### Quick Test (All Endpoints)

```bash
python test_phase2_endpoints.py
```

**Interactive prompts:**
- CEO OTP (6 digits)
- Vendor OTP (8 characters)

### OCR Workflow Test

```bash
python test_ocr_workflow.py
```

**Interactive prompts:**
- Vendor OTP (8 characters)

**Test scenarios run automatically:**
1. ✅ Low amount auto-approve (₦50,000)
2. ✅ High amount escalation (₦1,500,000)
3. ✅ OCR mismatch flagging (₦75,000 order vs ₦50,000 receipt)

---

## 📊 Expected Outputs

### Successful Test Output

```
╔════════════════════════════════════════════════════════════════════════════╗
║         TrustGuard Phase 2 Endpoint Testing Suite                         ║
║         OCR Auto-Approval + Backend 100% Validation                        ║
╚════════════════════════════════════════════════════════════════════════════╝

ℹ API Base URL: https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod

================================================================================
                        Authentication Tests
================================================================================

✓ CEO authenticated successfully. Token: eyJhbGciOiJIUzI1NiIs...
✓ Vendor authenticated successfully. Token: eyJhbGciOiJIUzI1NiIs...

================================================================================
                   CEO Chatbot Configuration Tests
================================================================================

✓ GET chatbot settings successful
✓ PUT chatbot settings successful
✓ Chatbot settings verified successfully

...

Overall: 7/7 tests passed
```

### OCR Workflow Output

```
╔════════════════════════════════════════════════════════════════════════════╗
║         TrustGuard OCR Auto-Approval Workflow Test Suite                  ║
╚════════════════════════════════════════════════════════════════════════════╝

================================================================================
SCENARIO 1: Low Amount Auto-Approve (OCR Valid)
================================================================================

[Step 1] Creating test order
✓ Order created: order_1732099123_abc123
ℹ Amount: ₦50,000.00

[Step 2] Uploading receipt to S3
✓ Receipt uploaded to S3: receipts/ceo_test_001/vendor_123/order_1732099123_abc123/receipt_1732099125.png

[Step 3] Triggering Textract OCR processing
✓ Textract OCR completed
ℹ Extracted 12 text blocks

[Step 4] Checking auto-approval result
ℹ Waiting for auto-approval processing (10 seconds)...
✓ Order status: approved
ℹ OCR Confidence: 87.5%
ℹ OCR Amount: ₦50,000.00
✓ ✓ Auto-approval logic worked correctly: approved

...

Overall: 3/3 scenarios passed
```

---

## 🧪 Test Coverage

### Endpoints Tested

| Endpoint | Method | Test Coverage |
|----------|--------|---------------|
| `/ceo/chatbot/settings` | GET/PUT | ✅ Read/Write config |
| `/vendor/preferences` | GET/PUT | ✅ Read/Write preferences |
| `/ceo/vendors` | GET | ✅ Risk score calculation |
| `/vendor/analytics/orders-by-day` | GET | ✅ Time-series data |
| `/ceo/analytics/fraud-trends` | GET | ✅ Time-series data |
| `/vendor/notifications/unread` | GET | ✅ Polling logic |
| `/vendor/orders/{id}` | GET | ✅ OCR results |

### OCR Scenarios Tested

| Scenario | Expected Outcome | Status |
|----------|------------------|--------|
| Low amount + Valid OCR | Auto-approve | ✅ Tested |
| High amount (≥₦1M) | Escalate to CEO | ✅ Tested |
| OCR amount mismatch | Flag for manual review | ✅ Tested |
| Low OCR confidence | Flag for manual review | ⏳ Manual test |
| Missing receipt data | Flag for manual review | ⏳ Manual test |

---

## 🐛 Troubleshooting

### Authentication Errors

**Problem:** `401 Unauthorized` or `Invalid OTP`

**Solution:**
1. Request fresh OTP via API:
   ```bash
   curl -X POST https://API_URL/auth/ceo/request-otp \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+2348012345678"}'
   ```
2. Check OTP format:
   - CEO: 6 characters (digits + symbols)
   - Vendor: 8 characters (alphanumeric + symbols)

### AWS Permissions Errors

**Problem:** `AccessDenied` for S3/Textract

**Solution:**
1. Verify IAM role/user has required permissions:
   - `s3:PutObject` on `trustguard-receipts-*`
   - `textract:DetectDocumentText`
   - `dynamodb:GetItem`, `dynamodb:PutItem` on TrustGuard tables

2. Check AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

### OCR Not Triggering

**Problem:** Order status stays `pending`, OCR not running

**Solution:**
1. Check S3 event notifications are configured
2. Verify Lambda function `TextractWorker` is triggered by S3 events
3. Check CloudWatch logs for Lambda errors:
   ```bash
   aws logs tail /aws/lambda/TextractWorker --follow
   ```

### Test Timeouts

**Problem:** `requests.exceptions.Timeout`

**Solution:**
1. Increase timeout in test scripts (default: 30s)
2. Check API Gateway/Lambda cold start delays
3. Verify network connectivity to AWS

---

## 📝 Adding New Tests

### Example: Test New Endpoint

```python
def test_new_endpoint():
    """Test description"""
    print_header("New Endpoint Test")
    
    # Make request
    response = make_request("GET", "/new/endpoint", token=vendor_token)
    
    # Validate response
    if response["success"]:
        data = response["data"].get("data", {})
        # Assertions here
        print_success("Test passed")
        return True
    else:
        print_error(f"Test failed: {response['data']}")
        return False
```

Add to test suite in `main()`:
```python
tests = [
    # ... existing tests
    ("New Endpoint", test_new_endpoint),
]
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend/tests
          pip install -r requirements.txt
      
      - name: Run endpoint tests
        env:
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
          TEST_CEO_PHONE: ${{ secrets.TEST_CEO_PHONE }}
          TEST_VENDOR_PHONE: ${{ secrets.TEST_VENDOR_PHONE }}
        run: |
          cd backend/tests
          python test_phase2_endpoints.py
```

---

## 📞 Support

If tests fail or you encounter issues:

1. Check CloudWatch Logs for Lambda errors
2. Verify DynamoDB table structure matches schema
3. Review API Gateway request/response logs
4. Check S3 bucket permissions and event notifications

**Common Issues:**
- ❌ Token expiration (default: 24h) → Request new OTP
- ❌ Missing environment variables → Check `.env` file
- ❌ AWS credentials not configured → Run `aws configure`
- ❌ S3 event not triggering Lambda → Check CloudFormation stack

---

## ✅ Success Criteria

All tests should pass before frontend development:

- ✅ CEO can configure chatbot settings
- ✅ Vendor can set OCR preferences
- ✅ Risk scores calculated correctly
- ✅ Analytics return time-series data
- ✅ Notifications return unread count
- ✅ **OCR auto-approval works for all scenarios**

**Backend 100% Complete** = All 7/7 endpoint tests + 3/3 OCR scenarios passing.
