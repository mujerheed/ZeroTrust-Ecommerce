# TrustGuard Testing Checklist
**Date:** November 23, 2025  
**Purpose:** Comprehensive testing for multi-role login, OTP improvements, and feature validation

---

## 🔐 OTP Improvements (✅ Completed)

### Features Implemented:
1. **Auto-Validation**: OTP automatically submits when all digits are entered
   - Vendor: 8 characters
   - CEO: 6 characters
   - No need to click "Verify" button

2. **Password Masking**: OTP input shows `•••••` instead of plain text
   - Type: `password` for security
   - Prevents shoulder surfing

### Files Modified:
- ✅ `/frontend/components/ui/otp-input.tsx` - Added `masked` prop
- ✅ `/frontend/app/vendor/login/page.tsx` - Auto-submit + masking
- ✅ `/frontend/app/ceo/login/page.tsx` - Auto-submit + masking
- ✅ `/frontend/app/ceo/signup/page.tsx` - Auto-submit + masking

---

## 🧪 Test Plan

### Test 1: Multi-Role Login (Simultaneous Sessions)

**Objective:** Verify CEO and Vendor can login simultaneously without conflicts

**🔑 CURRENT TEST CREDENTIALS (Ready to Use):**

**CEO Login (Tab 1):**
- URL: `http://localhost:3001/ceo/login`
- Email: `wadip30466@aikunkun.com`
- OTP: `9%^73!` (6 characters)
- CEO ID: `ceo_1763735768748`

**Vendor Login (Tab 2):**
- URL: `http://localhost:3001/vendor/login`
- Phone: `+2348133336318`
- OTP: `nRP#4a9s` (8 characters)
- Vendor ID: `ceo_test_001`

**Steps:**
1. Open browser Tab 1 → Navigate to `http://localhost:3001/ceo/login`
2. Login as CEO:
   - Enter email: `wadip30466@aikunkun.com`
   - Click "Send OTP"
   - Enter OTP: `9%^73!` (will auto-submit when 6 digits entered)
   - Verify: OTP shows as `••••••` (masked)
   - Verify: Redirects to CEO dashboard
   - Verify: Session timer appears in top bar

3. Open browser Tab 2 (same browser) → Navigate to `http://localhost:3001/vendor/login`
4. Login as Vendor:
   - Enter phone: `+2348133336318`
   - Click "Send OTP"
   - Enter OTP: `nRP#4a9s` (will auto-submit when 8 digits entered)
   - Verify: OTP shows as `••••••••` (masked)
   - Verify: Redirects to Vendor dashboard
   - Verify: Session timer appears in top bar

5. Verify Both Tabs Work Independently:
   - Tab 1 (CEO): Still logged in? Session timer running? ✅
   - Tab 2 (Vendor): Still logged in? Session timer running? ✅
   - Check localStorage (F12 → Application → Local Storage):
     * `ceo_token` exists ✅
     * `vendor_token` exists ✅
     * `ceo_session_start` exists ✅
     * `vendor_session_start` exists ✅
   - Logout from Tab 1 (CEO) → Tab 2 (Vendor) still logged in? ✅
   - Re-login to Tab 1 (CEO) → Both tabs work? ✅

**Expected Results:**
✅ Both tabs remain logged in  
✅ Separate localStorage keys:
  - Tab 1: `ceo_token`, `ceo_session_start`, `ceo_id`
  - Tab 2: `vendor_token`, `vendor_session_start`, `vendor_id`
✅ No authentication conflicts  
✅ Session timers run independently (60 minutes each)

**Check LocalStorage (F12 → Application → Local Storage):**
```
ceo_token: "eyJhbGciOiJIUzI1NiIs..."
ceo_session_start: "1763917xxx"
ceo_id: "ceo_test_001"
vendor_token: "eyJhbGciOiJIUzI1NiIs..."
vendor_session_start: "1763917xxx"
vendor_id: "vendor_test_001"
```

---

### Test 2: OTP Auto-Validation

**Objective:** Verify OTP auto-submits without clicking button

**Steps:**
1. Navigate to `/vendor/login`
2. Enter phone number, click "Send OTP"
3. When OTP input appears:
   - Type/paste 8 characters
   - DO NOT click "Verify & Login" button
   - OTP should auto-submit after 8th character

**Expected Results:**
✅ Auto-redirect to dashboard after entering 8 digits  
✅ No manual button click needed  
✅ Toast notification: "Login successful"

**Repeat for:**
- CEO Login (6 digits)
- CEO Signup (6 digits)

---

### Test 3: OTP Password Masking

**Objective:** Verify OTP displays as `••••••` for security

**Steps:**
1. Navigate to `/vendor/login`
2. Enter phone number, click "Send OTP"
3. In OTP input, type any character
4. Verify character displays as `•` (dot/bullet)
5. Type remaining characters
6. All should show as `••••••••`

**Expected Results:**
✅ Each OTP box shows `•` instead of actual character  
✅ Cannot see OTP value (shoulder surfing protection)  
✅ Auto-submit still works with masked input

---

### Test 4: Vendor Preferences (Graceful Fallback)

**Objective:** Verify preferences work without DynamoDB table

**Steps:**
1. Login as vendor
2. Navigate to Vendor Dashboard → Settings (if exists) or use API directly
3. Try to save preferences:
   ```bash
   curl -X PUT http://localhost:8000/vendor/preferences \
     -H "Authorization: Bearer <vendor_token>" \
     -H "Content-Type: application/json" \
     -d '{"auto_approve_threshold": 5000, "textract_enabled": true}'
   ```

**Expected Results:**
✅ Returns HTTP 200 (not 500)  
✅ Returns default preferences object:
```json
{
  "status": "success",
  "data": {
    "vendor_id": "vendor_xxx",
    "auto_approve_threshold": 5000,
    "textract_enabled": true,
    "updated_at": 1763917xxx
  }
}
```
✅ Warning in backend logs: "VendorPreferences table not found"

---

### Test 5: Verification Status

**Objective:** Verify vendors show correct "Verified" badge after first OTP login

**Steps:**
1. Login as CEO
2. Navigate to `/ceo/vendors`
3. Check vendor list table
4. Vendors who have logged in with OTP should show:
   - Badge: "✓ Verified" (green)
5. Vendors who were just created but never logged in:
   - Badge: "✗ Unverified" (gray)

**Expected Results:**
✅ `vendor_1763814333_93b06595` shows "Verified" (manually set to true)  
✅ `vendor_test_001` shows "Unverified" (never logged in)  
✅ Backend auto-marks `verified: true` on first OTP login

---

### Test 6: Session Timer

**Objective:** Verify 60-minute auto-logout timer works

**Steps:**
1. Login as Vendor or CEO
2. Check TopBar for timer display
3. Wait and observe:
   - Timer counts down from 60:00
   - At 5:00 remaining → background turns yellow (warning)
   - At 0:00 → auto-logout + redirect to login with `?expired=true`

**Fast Test (Optional):**
- Open DevTools Console
- Type: `localStorage.setItem('vendor_session_start', Date.now() - 59.5*60*1000)`
- Refresh page
- Timer should show ~0:30 and trigger warning/logout

**Expected Results:**
✅ Timer visible in TopBar  
✅ Yellow warning at 5 minutes  
✅ Auto-logout at 0 minutes  
✅ Redirect to login page

---

### Test 7: Dashboard Real Data

**Objective:** Verify dashboard shows actual backend data (not mocks)

**Steps:**
1. Login as Vendor
2. Navigate to Dashboard
3. Check:
   - Total Orders count
   - Pending/Completed orders
   - Revenue metrics
   - Charts (Orders by Day)

**Verify API Calls (F12 → Network Tab):**
✅ `GET /vendor/orders` - should return real orders  
✅ `GET /vendor/analytics/orders-by-day` - should return chart data  
✅ `GET /vendor/notifications/unread` - should return notifications

**Expected Results:**
✅ No "mock" data indicators  
✅ Real numbers from DynamoDB  
✅ Charts update based on actual orders

---

### Test 8: Receipt Metadata Enhancement

**Objective:** Add checksum, Textract warnings, OCR confidence scores

**Steps:**
1. Login as Vendor
2. Navigate to `/vendor/receipts`
3. Check receipt details should show:
   - Receipt checksum/hash (SHA-256)
   - Textract OCR data (if enabled):
     - Detected amount vs expected amount
     - Confidence score (0-100%)
     - Bank name extracted
     - Date extracted
   - Mismatch warnings (if amounts differ)

**Expected Enhancements:**
- [ ] Receipt checksum display
- [ ] Textract confidence score badge
- [ ] Mismatch warning alert (amount differs)
- [ ] Bank verification status

---

## 🐛 Known Issues & Fixes Applied

### ✅ Fixed Issues:
1. **Session Conflict** - Both roles sharing same session key
   - Fix: Role-specific keys (`vendor_session_start`, `ceo_session_start`)

2. **Token Conflict** - Second login overwrites first JWT
   - Fix: Role-specific tokens (`vendor_token`, `ceo_token`)

3. **Vendor Preferences 500 Error** - VendorPreferences table doesn't exist
   - Fix: Graceful fallback with default preferences

4. **Verification Status** - Vendors showing "Unverified" after login
   - Fix: Auto-mark `verified: true` on first OTP login (backend)

5. **Missing Session Timer** - CEO portal had no timer
   - Fix: Added timer to CEO TopBar matching Vendor

---

## 📊 Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Multi-Role Login | ⏳ Pending | Need to test in browser |
| OTP Auto-Submit | ✅ Implemented | Vendor: 8 chars, CEO: 6 chars |
| OTP Masking | ✅ Implemented | Shows `••••••` |
| Vendor Preferences | ✅ Fixed | Graceful fallback added |
| Verification Status | ✅ Fixed | Auto-marks on first login |
| Session Timer | ✅ Fixed | Both CEO & Vendor have timer |
| Dashboard Data | ⏳ Pending | Need to verify real data |
| Receipt Metadata | ⏳ Pending | Enhancements needed |

---

## 🚀 Next Steps

1. **Run all tests above in browser** ✓ Ready to test
2. **Receipt metadata enhancements** - Add checksum, Textract warnings
3. **Dashboard charts** - Replace mock data with real API calls
4. **Meta OAuth** - Configure WhatsApp/Instagram integration
5. **Deploy to AWS** - SAM deployment with DynamoDB tables

---

## 📝 Developer Notes

**Backend Running:**
- Port: 8000
- Command: `cd backend && ./venv/bin/uvicorn app:app --reload --port 8000`
- Logs: Check terminal for OTP codes with 🔑 emoji

**Frontend Running:**
- Port: 3001 (or 3000)
- Command: `cd frontend && npm run dev`
- Access: `http://localhost:3001`

**Test Accounts:**
- CEO: `ceo_test_001` (email: ceo@test.com)
- Vendor: `vendor_test_001` (phone: +2348133336318)
- Vendor: `vendor_1763814333_93b06595` (phone: check DB)

**Check Backend Logs for OTP:**
```
🔑 DEV OTP: Ab3$Xy9!
```

---

**Ready to test!** Start with Test 1 (Multi-Role Login) 🎯
