# TrustGuard Codebase Audit & Cleanup Checklist

**Date:** 2025-11-23  
**Status:** In Progress

---

## 🔍 **Frontend Audit**

### ✅ **Build Errors Fixed**
1. ✅ **CEO Approvals Page**: Fixed `useSearchParams()` Suspense boundary warning
   - Wrapped component in `<Suspense>` fallback
   - Separated content component from export

### 🗂️ **File Cleanup Needed**

#### **Duplicate/Unused Files**
1. ❌ **`frontend/components/vendor/sidebar.tsx`** - REMOVE
   - **Reason**: Replaced by `sidebar-new.tsx`
   - **Verification**: No imports found via grep search
   - **Action**: Delete file

#### **Backend Documentation Files** (Move to `/docs`)
1. ⚠️ **`backend/BUYER_AUTH_COMPLETION_REPORT.md`**
2. ⚠️ **`backend/BUYER_AUTH_IMPLEMENTATION.md`**
3. ⚠️ **`backend/CEO_SERVICE_COMPLETION_REPORT.md`**
4. ⚠️ **`backend/CRITICAL_FEATURES_IMPLEMENTATION_SUMMARY.md`**
5. ⚠️ **`backend/FEATURE_GAP_ANALYSIS.md`**
6. ⚠️ **`backend/LOCAL_TEST_RESULTS.md`**
7. ⚠️ **`backend/ORDER_SERVICE_COMPLETION_REPORT.md`**
8. ⚠️ **`backend/RECEIPT_IMPLEMENTATION_SUMMARY.md`**
   - **Action**: Move to `/docs/backend/` folder

#### **Test Files** (Organize in `/backend/tests/`)
1. ⚠️ **`backend/test_buyer_auth_e2e.py`**
2. ⚠️ **`backend/test_ceo_e2e.py`**
3. ⚠️ **`backend/test_ceo_escalation_manual.py`**
4. ⚠️ **`backend/test_critical_features_e2e.py`**
5. ⚠️ **`backend/test_order_e2e.py`**
6. ⚠️ **`backend/test_otp_debug.py`**
7. ⚠️ **`backend/test_receipt_pipeline_e2e.py`**
8. ⚠️ **`backend/test_textract_ocr_local.py`**
   - **Action**: Move to `/backend/tests/e2e/` folder

#### **Debug Scripts** (Organize in `/backend/debug/`)
1. ⚠️ **`backend/debug_phone.py`**
   - **Action**: Move to `/backend/debug/` folder

---

## 📋 **Missing Features Implementation**

### **Frontend Priority Tasks**

#### **HIGH PRIORITY**

1. ⏳ **Receipt Metadata Enhancements**
   - **File**: `frontend/app/vendor/receipts/page.tsx`
   - **Features**:
     - Display SHA-256 checksum in receipt details
     - Show Textract mismatch warnings:
       - Amount discrepancy badge (if extracted ≠ submitted)
       - Vendor name mismatch alert
       - Confidence score indicator
   - **Estimated Time**: 2 hours
   - **Status**: Not Started

2. ⏳ **Dashboard Chart Real Data**
   - **File**: `frontend/app/vendor/dashboard/page.tsx`
   - **Features**:
     - Replace mock data with `/vendor/analytics/orders-by-day` API call
     - Add date range selector (7d, 30d, 90d)
     - Show loading skeleton while fetching
   - **Estimated Time**: 30 minutes
   - **Status**: Not Started

#### **MEDIUM PRIORITY**

3. ⏳ **Date Range Filter on Dashboard**
   - **File**: `frontend/app/vendor/dashboard/page.tsx`
   - **Features**:
     - shadcn/ui DateRangePicker component
     - Filter orders table by created_at range
     - Persist selection in URL params
   - **Estimated Time**: 2 hours
   - **Status**: Not Started

4. ⏳ **CEO Post-Registration Flows**
   - **Files**:
     - `frontend/app/ceo/onboarding/meta-connect/page.tsx` (NEW)
     - `frontend/app/ceo/settings/chatbot/page.tsx` (NEW)
     - `frontend/app/ceo/settings/profile/page.tsx` (NEW)
   - **Features**:
     - Meta OAuth for WhatsApp + Instagram
     - Chatbot customization (greeting, tone, Pidgin support)
     - Profile management with OTP re-auth
   - **Estimated Time**: 6-8 hours
   - **Status**: Not Started

---

## 🔧 **Backend Audit**

### **API Endpoint Verification**

#### **Vendor Service Endpoints**
- ✅ `GET /vendor/dashboard`
- ✅ `GET /vendor/orders`
- ✅ `GET /vendor/receipts/{order_id}`
- ✅ `POST /vendor/orders/{order_id}/verify`
- ✅ `GET /vendor/buyers`
- ✅ `GET /vendor/buyers/{buyer_id}`
- ✅ `POST /vendor/orders/{order_id}/messages`
- ✅ `GET /vendor/orders/{order_id}/messages`
- ✅ `GET /vendor/preferences`
- ✅ `PUT /vendor/preferences`
- ⚠️ `GET /vendor/notifications/unread` - **Verify exists**
- ⚠️ `GET /vendor/notifications/recent` - **Verify exists** (for toast polling)
- ⚠️ `GET /vendor/analytics/orders-by-day` - **Verify exists**

#### **CEO Service Endpoints**
- ✅ `GET /ceo/approvals`
- ✅ `POST /ceo/approvals/{order_id}/approve`
- ✅ `POST /ceo/approvals/{order_id}/reject`
- ⚠️ `POST /ceo/oauth/whatsapp/connect` - **Create new**
- ⚠️ `POST /ceo/oauth/instagram/connect` - **Create new**
- ⚠️ `GET /ceo/oauth/callback` - **Create new**
- ⚠️ `PUT /ceo/chatbot/settings` - **Create new**
- ⚠️ `GET /ceo/chatbot/settings` - **Create new**

#### **Auth Service Endpoints**
- ✅ `POST /auth/vendor/login`
- ✅ `POST /auth/verify-otp`
- ⚠️ `POST /auth/vendor/request-otp` - **Verify exists** (for OTP re-auth)

---

## 🧪 **Testing Plan**

### **Unit Tests**
- ⏳ Test session timeout logic (`frontend/lib/session.ts`)
- ⏳ Test OTP validation format (`backend/auth_service/utils.py`)
- ⏳ Test checksum generation (`backend/receipt_service/utils.py`)

### **Integration Tests**
- ⏳ Test vendor login → dashboard flow
- ⏳ Test receipt upload → verification flow
- ⏳ Test negotiation chat → order completion
- ⏳ Test CEO escalation → approval flow

### **End-to-End Tests**
1. **Buyer Flow (WhatsApp)**
   - ⏳ DM bot → OTP → Upload receipt → Confirmation
2. **Buyer Flow (Instagram)**
   - ⏳ DM bot → OTP → Upload receipt → Confirmation
3. **Vendor Flow**
   - ⏳ Login → View pending receipts → Approve → Chat buyer
4. **CEO Flow**
   - ⏳ Login → Review escalation → OTP re-auth → Approve

---

## 🚀 **Meta OAuth Configuration**

### **WhatsApp Business API Setup**
1. ⏳ Create Meta App (Business type)
2. ⏳ Add WhatsApp product
3. ⏳ Configure webhook URL: `https://api.trustguard.ng/integrations/webhook/whatsapp`
4. ⏳ Subscribe to messages, message_status events
5. ⏳ Generate test token (dev environment)
6. ⏳ Store in AWS Secrets Manager: `/meta/app/test-token`

### **Instagram Messaging API Setup**
1. ⏳ Add Instagram product to same Meta App
2. ⏳ Configure webhook URL: `https://api.trustguard.ng/integrations/webhook/instagram`
3. ⏳ Subscribe to messages, messaging_postbacks events
4. ⏳ Generate test token (dev environment)
5. ⏳ Store in AWS Secrets Manager: `/meta/app/instagram-test-token`

### **OAuth Flow Implementation**
1. ⏳ Backend: Create `/ceo/oauth/whatsapp/connect` endpoint
   - Redirect to Meta OAuth with `whatsapp_business_messaging` scope
2. ⏳ Backend: Create `/ceo/oauth/instagram/connect` endpoint
   - Redirect to Meta OAuth with `instagram_basic` scope
3. ⏳ Backend: Create `/ceo/oauth/callback` endpoint
   - Exchange code for long-lived token
   - Store in Secrets Manager keyed by `ceo_id`
   - Map `phone_number_id` / `page_id` → `ceo_id` in DynamoDB
4. ⏳ Frontend: Create onboarding wizard
   - Step 1: Connect WhatsApp
   - Step 2: Connect Instagram
   - Step 3: Customize chatbot
   - Step 4: Complete setup

---

## 📊 **Progress Tracking**

### **Overall Completion**
- **Frontend**: 80% (20/25 features)
- **Backend**: 85% (17/20 features)
- **Meta Integration**: 0% (not started)
- **Testing**: 10% (basic tests only)

### **Critical Path to Production**
1. ✅ Fix build errors
2. ⏳ Implement missing API endpoints
3. ⏳ Meta OAuth configuration
4. ⏳ End-to-end testing
5. ⏳ Deploy to staging
6. ⏳ Real-world testing with live WhatsApp/Instagram
7. ⏳ Production deployment

---

## ❓ **Clarification Questions**

### **For User**
1. **Meta App Credentials**: Do you already have a Meta App ID and Secret, or should we create one together?
2. **Testing Environment**: Should we use Meta's test mode or sandbox numbers for initial testing?
3. **Multi-CEO Tenancy**: How many CEOs should the system support initially? (affects OAuth token storage strategy)
4. **Textract**: Should we enable Amazon Textract for ALL vendors by default, or make it opt-in per CEO?
5. **High-Value Threshold**: Confirm ₦1,000,000 (₦1M) is the correct threshold for CEO escalation?
6. **Pidgin Support**: Should the chatbot auto-detect language or require CEO to set it during onboarding?
7. **Session Timeout**: Confirm 60 minutes is acceptable for vendor sessions (can't be extended with activity)?

### **Technical Decisions**
1. **Token Rotation**: Should Meta OAuth tokens auto-rotate before 60-day expiry, or wait for manual CEO re-auth?
2. **Webhook Verification**: Use HMAC-SHA256 signature verification for all incoming Meta webhooks?
3. **Rate Limiting**: Apply rate limits to chatbot responses (e.g., max 10 messages/minute per buyer)?
4. **Audit Log Retention**: How long to keep audit logs? (7 days? 90 days? Forever?)

---

## 📝 **Next Immediate Actions**

**Priority 1 (Critical):**
1. ✅ Fix CEO approvals Suspense error
2. ⏳ Remove unused `sidebar.tsx` file
3. ⏳ Verify all backend API endpoints match frontend expectations
4. ⏳ Test backend with live requests

**Priority 2 (High):**
5. ⏳ Implement receipt metadata enhancements
6. ⏳ Connect dashboard chart to real API
7. ⏳ Create Meta OAuth endpoints

**Priority 3 (Testing):**
8. ⏳ Write end-to-end test scenarios
9. ⏳ Test with local backend running
10. ⏳ Document test results

---

**Last Updated:** 2025-11-23  
**Next Review:** After backend API verification
