# Vendor Frontend Implementation Plan

**Based on User Stories V-01, V-02, V-03**

## Component Structure (5 Pages + 1 Modal)

### 1. 🔐 Login Page (V-01) - EXISTING
**File**: `app/vendor/login/page.tsx`  
**Status**: ✅ Already Implemented  
**Features**:
- 8-character OTP input via SMS/WhatsApp
- Phone number entry → OTP verification
- JWT token storage (60-min expiry per backend)
- Redirect to dashboard on success

**User Story Coverage**: V-01 ✅

---

### 2. 🏠 Dashboard (Overview) - ENHANCE EXISTING
**File**: `app/vendor/dashboard/page.tsx`  
**Status**: 🚧 Needs Enhancement  
**Current**: Basic KPI cards + pending orders table  
**Enhancements Needed**:
- Real-time notifications (poll `/vendor/notifications/unread` every 30s)
- Analytics chart (orders-by-day from `/vendor/analytics/orders-by-day`)
- Quick actions: "View Pending Receipts" → navigate to /vendor/receipts
- Navigation sidebar to all 5 pages
- Preferences modal (floating gear icon)

**API Endpoints**:
- GET `/vendor/dashboard` ✅
- GET `/vendor/notifications/unread` ✅
- GET `/vendor/analytics/orders-by-day?days=7` ✅

---

### 3. 🧾 Receipt Verification (V-03) - NEW
**File**: `app/vendor/receipts/page.tsx`  
**Status**: ❌ Not Created  
**Features**:
- Tabs: Pending Review | Approved | Flagged
- Receipt image viewer (S3 pre-signed URL)
- Textract OCR results (if enabled)
  - Amount match indicator
  - Date/timestamp verification
  - Bank reference extraction
  - Confidence score badge
- Manual review checklist:
  - [ ] Amount verified
  - [ ] Date correct
  - [ ] Bank details match
- Actions: ✅ Approve | ⚠️ Flag for CEO | ❌ Reject
- Navigation: Previous/Next receipt (keyboard arrows)
- Filter by status, vendor, date range

**API Endpoints**:
- GET `/vendor/receipts/{order_id}` - Get receipt details + S3 URL
- POST `/vendor/orders/{order_id}/verify` - Approve/flag/reject
  ```json
  {
    "action": "approve" | "flag" | "reject",
    "notes": "Amount mismatch: Expected ₦45,000 but receipt shows ₦40,000"
  }
  ```
- GET `/vendor/preferences` - Check if textract_enabled

**UI Components**:
- ReceiptImageViewer (zoom, pan, fullscreen)
- TextractResultsCard (OCR data with confidence badges)
- ManualReviewChecklist
- ActionButtons (approve/flag/reject with confirmation)

**User Story Coverage**: V-03 ✅

---

### 4. 👥 Buyers Management - NEW
**File**: `app/vendor/buyers/page.tsx`  
**Status**: ❌ Not Created  
**Features**:
- List all buyers with stats:
  - Total orders
  - Last interaction timestamp
  - Flag status (clean vs flagged)
  - Masked phone number (+234***1234)
- Filter: Show Flagged Only toggle
- Search by buyer_id or phone
- Click buyer → drill-down view:
  - Buyer details
  - Order history (last 10)
  - Statistics: total, completed, flagged, pending

**API Endpoints**:
- GET `/vendor/buyers?flag_status=flagged&limit=50` ✅
- GET `/vendor/buyers/{buyer_id}` ✅

**UI Components**:
- BuyersTable (sortable, filterable)
- BuyerDetailsModal (order history, stats)
- FlagBadge (visual indicator for flagged buyers)

---

### 5. 💬 Negotiation/Chat (V-02) - NEW
**File**: `app/vendor/negotiation/[order_id]/page.tsx`  
**Status**: ❌ Not Created  
**Features**:
- Chat interface (buyer ↔ vendor)
- Messages sent via CEO's Meta token (WhatsApp/Instagram)
- Buyer sees business handle (@adasfashion) not vendor personal number
- Quick actions:
  - 💰 Confirm Price → "✅ Price confirmed: ₦X,XXX"
  - 💳 Send Payment Details → Bank/Account/Amount/Reference
  - 📸 Request Receipt → "Please upload your payment receipt"
- Message history (last 50 messages)
- Real-time updates (poll every 10s when chat open)
- Platform indicator (WhatsApp vs Instagram icon)

**API Endpoints**:
- POST `/vendor/orders/{order_id}/messages` ✅
  ```json
  {
    "message": "Your order is ready for payment",
    "quick_action": "send_payment_details" | "confirm_price" | "request_receipt"
  }
  ```
- GET `/vendor/orders/{order_id}/messages?limit=50` ✅

**UI Components**:
- ChatBubble (buyer vs vendor styling)
- QuickActionButtons (3 buttons for common messages)
- MessageInput (textarea + send button)
- PlatformBadge (WhatsApp/Instagram icon)
- TimeAgo component ("2h ago", "3d ago")

**User Story Coverage**: V-02 ✅

---

### 6. 📦 Orders List - ENHANCE EXISTING
**File**: `app/vendor/orders/page.tsx` (might need to create)  
**Current**: Embedded in dashboard  
**Enhancements**:
- Dedicated page for all orders (not just pending)
- Status filter dropdown: All | Pending | Approved | Flagged | Rejected
- Search by order_id or buyer_name
- Pagination (load more)
- Click order → navigate to `/vendor/negotiation/{order_id}`

**API Endpoints**:
- GET `/vendor/orders?status=PENDING&limit=20` ✅
- GET `/vendor/search?q=john` ✅

---

### 7. ⚙️ Preferences Modal - NEW COMPONENT
**File**: `components/vendor/preferences-modal.tsx`  
**Status**: ❌ Not Created  
**Features**:
- Floating gear icon (bottom-right corner)
- Modal/slide-out panel
- Settings:
  - **Auto-Approve Threshold**: Input field (₦0 - ₦1,000,000)
    - Helper text: "Receipts below this amount are auto-approved"
  - **Textract OCR**: Toggle switch (ON/OFF)
    - Helper text: "Enable automated receipt verification"
  - [Save Changes] button

**API Endpoints**:
- GET `/vendor/preferences` ✅
- PUT `/vendor/preferences` ✅
  ```json
  {
    "auto_approve_threshold": 500000,  // ₦5,000 in kobo
    "textract_enabled": true
  }
  ```

---

## Global Components

### Navigation Sidebar
**File**: `components/vendor/sidebar.tsx`  
**Items**:
1. 🏠 Dashboard
2. 📦 Orders
3. 🧾 Receipts (with pending count badge)
4. 👥 Buyers
5. 💬 Negotiation
6. ⚙️ Preferences (modal trigger)
7. 🚪 Logout (bottom)

### Header
**File**: `components/vendor/header.tsx`  
**Features**:
- Vendor name + business name
- Notification bell (unread count from `/vendor/notifications/unread`)
- Session timer (JWT expiry countdown)
- Logout button

---

## Technical Stack

**Frontend**:
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React Hook Form + Zod validation
- Axios for API calls
- Sonner for toast notifications

**State Management**:
- React Context for vendor session
- SWR for data fetching (auto-refresh)
- Local state for forms

**Authentication**:
- JWT token in localStorage
- Axios interceptor for Authorization header
- Token refresh at 50 minutes (backend JWT expires at 60min)
- Auto-logout on 401

---

## Implementation Order

**Phase 1**: Core Functionality (V-01, V-03)
1. ✅ Login Page (already done)
2. 🧾 Receipt Verification Page (HIGH PRIORITY - core fraud prevention)
3. ⚙️ Preferences Modal (needed for Textract toggle)

**Phase 2**: Communication (V-02)
4. 💬 Negotiation/Chat Page
5. 🔔 Real-time notifications (polling)

**Phase 3**: Management & Analytics
6. 👥 Buyers Management Page
7. 📦 Enhanced Orders List
8. 📊 Dashboard Analytics Chart

**Phase 4**: Polish
9. 🎨 Navigation Sidebar
10. ⏱️ Session Timer in Header
11. 🔍 Search & Filters
12. ♿ Accessibility (keyboard navigation for receipt review)

---

## API Integration Summary

**All Required Endpoints**:
✅ POST `/auth/vendor/login` - Send OTP  
✅ POST `/auth/verify-otp` - Verify OTP, get JWT  
✅ GET `/vendor/dashboard` - KPIs, pending orders  
✅ GET `/vendor/orders` - List orders with filters  
✅ GET `/vendor/receipts/{order_id}` - Receipt details + S3 URL  
✅ POST `/vendor/orders/{order_id}/verify` - Approve/flag/reject  
✅ GET `/vendor/buyers` - List buyers with stats  
✅ GET `/vendor/buyers/{buyer_id}` - Buyer details  
✅ POST `/vendor/orders/{order_id}/messages` - Send chat message  
✅ GET `/vendor/orders/{order_id}/messages` - Chat history  
✅ GET `/vendor/preferences` - Get settings  
✅ PUT `/vendor/preferences` - Update settings  
✅ GET `/vendor/notifications/unread` - New notifications  
✅ GET `/vendor/analytics/orders-by-day` - Chart data  
✅ GET `/vendor/search` - Search orders  

**Backend Status**: 100% Complete ✅

---

## Next Steps

1. Create Receipt Verification Page (V-03)
2. Create Negotiation/Chat Page (V-02)
3. Create Buyers Management Page
4. Create Preferences Modal
5. Enhance Dashboard with analytics chart
6. Add navigation sidebar
7. Add real-time notifications polling
8. Test end-to-end workflow

**Let's start with Receipt Verification (most critical for fraud prevention)!**
