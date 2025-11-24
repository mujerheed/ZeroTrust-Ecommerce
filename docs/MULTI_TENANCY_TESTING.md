# Multi-Tenancy Security Testing Guide

## 🔒 What We're Testing

This test verifies that different CEO accounts cannot access each other's data - a critical Zero Trust security requirement.

## Prerequisites

1. **Backend must be running** on `http://localhost:8000`
2. **Python 3** with `requests` library

## Step 1: Start the Backend

```bash
cd backend
./venv/bin/uvicorn app:app --reload --port 8000
```

**Verify it's running:**
```bash
curl http://localhost:8000/
# Should return: {"message":"TrustGuard API is running"}
```

## Step 2: Install Dependencies (if needed)

```bash
pip install requests
```

## Step 3: Run the Test Suite

```bash
cd /path/to/ZeroTrust-Ecommerce
python3 test_multi_tenancy.py
```

## What the Test Does

### 1. **Creates 2 CEO Accounts**
   - **CEO_A**: Alice CEO (Alice's Business Empire)
   - **CEO_B**: Bob CEO (Bob's Commerce Hub)

### 2. **Tests Vendor Isolation**
   - Creates a vendor for CEO_A
   - Creates a vendor for CEO_B
   - ✅ **Verifies**: CEO_A cannot see CEO_B's vendor in their vendor list
   - ✅ **Verifies**: CEO_A gets 403/404 when trying to access CEO_B's vendor details

### 3. **Tests Notification Isolation**
   - Creates a test notification for CEO_B
   - ✅ **Verifies**: CEO_A cannot see CEO_B's notifications

### 4. **Tests Analytics Isolation**
   - Fetches analytics for both CEOs
   - ✅ **Verifies**: Each CEO sees only their own vendor performance data

## Expected Output

```
╔══════════════════════════════════════════════════════════════╗
║     TrustGuard Multi-Tenancy Security Test Suite            ║
║     Testing Zero Trust Data Isolation                        ║
╚══════════════════════════════════════════════════════════════╝

[HH:MM:SS] HEADER: 🔒 MULTI-TENANCY SECURITY TEST SUITE
[HH:MM:SS] INFO: Testing data isolation between CEO accounts...

[HH:MM:SS] HEADER: Step 1: Creating CEO test accounts...
[HH:MM:SS] HEADER: Creating CEO account: Alice CEO (Alice's Business Empire)
[HH:MM:SS] SUCCESS: CEO registered: ceo_...
[HH:MM:SS] INFO: OTP received: 123456
[HH:MM:SS] SUCCESS: ✅ CEO logged in successfully! CEO ID: ceo_...

... (more output) ...

✅ Vendor Isolation - CEO_A cannot see CEO_B vendors: PASSED
✅ Vendor Isolation - CEO_A cannot access CEO_B vendor details: PASSED
✅ Notification Isolation - CEO_A cannot see CEO_B notifications: PASSED
✅ Analytics Isolation - Each CEO sees only their vendors: PASSED

============================================================
MULTI-TENANCY SECURITY TEST REPORT
============================================================

Summary:
  Total Tests: 4
  ✅ Passed: 4
  ❌ Failed: 0
  Success Rate: 100.0%

🎉 ALL TESTS PASSED - Multi-tenancy is properly isolated!

Report saved to: multi_tenancy_test_report.json
```

## Test Report

After running, a detailed JSON report is saved to:
```
multi_tenancy_test_report.json
```

This contains:
- Timestamp of test run
- Summary statistics
- Detailed results for each test
- Pass/fail status with reasons

## What If Tests Fail?

If any test fails, it indicates a **SECURITY VULNERABILITY**:

❌ **Vendor Isolation Failed** → CEO_A can see CEO_B's vendors
   - **Impact**: Data breach - businesses can see each other's vendor information
   - **Fix**: Check `ceo_id` filtering in `/ceo/vendors` endpoint

❌ **Notification Isolation Failed** → CEO_A can see CEO_B's notifications
   - **Impact**: CEO_A can see confidential escalation data from CEO_B
   - **Fix**: Check notification query filters by `ceo_id`

❌ **Analytics Isolation Failed** → Cross-tenant data leakage
   - **Impact**: CEOs can see competitor business metrics
   - **Fix**: Verify analytics aggregation queries filter by `ceo_id`

## Additional Manual Tests

### Test Order Isolation (Manual)

1. Create an order for CEO_A's vendor
2. Try to access it using CEO_B's token:
   ```bash
   curl -H "Authorization: Bearer <CEO_B_TOKEN>" \
     http://localhost:8000/ceo/orders/<CEO_A_ORDER_ID>
   ```
   **Expected**: 403 Forbidden or 404 Not Found

### Test Approval Isolation (Manual)

1. Create an escalation for CEO_A
2. Try to approve it using CEO_B's token:
   ```bash
   curl -X PATCH -H "Authorization: Bearer <CEO_B_TOKEN>" \
     http://localhost:8000/ceo/approvals/<CEO_A_ORDER_ID>/approve \
     -d '{"otp": "123456"}'
   ```
   **Expected**: 403 Forbidden

## Cleanup Test Data

To remove test CEO accounts after testing:

```python
# Delete CEO_A
DELETE /ceo/profile (with CEO_A token)

# Delete CEO_B  
DELETE /ceo/profile (with CEO_B token)
```

---

## Quick Start (Copy-Paste)

```bash
# Terminal 1: Start backend
cd backend
./venv/bin/uvicorn app:app --reload --port 8000

# Terminal 2: Run tests
cd /path/to/ZeroTrust-Ecommerce
python3 test_multi_tenancy.py
```

---

**🔐 Security Note**: Multi-tenancy isolation is critical for Zero Trust architecture. ALL tests must pass before production deployment.
