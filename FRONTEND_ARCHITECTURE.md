# TrustGuard Frontend Architecture & Implementation Plan

Based on the "Ada & Tunde" narrative, this document outlines the frontend architecture for the TrustGuard Zero Trust E-commerce system.

## 1. Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **UI Library**: shadcn/ui (Radix UI primitives)
- **State Management**: React Context + Hooks (Zustand if complex)
- **Icons**: Lucide React
- **Charts**: Recharts (for Analytics)
- **Forms**: React Hook Form + Zod

## 2. User Roles & Portals

The frontend will serve two primary distinct portals (Buyer interaction is via Chatbot, with a possible tracking page):

### A. Vendor Portal (`/vendor`)
Focused on order management, negotiation, and receipt verification.

### B. CEO Portal (`/ceo`)
Focused on business oversight, vendor management, high-value approvals, and system configuration.

---

## 3. Detailed Page Structure

### Public / Shared
- **Landing Page** (`/`): Brief intro, Login buttons for Vendor/CEO.
- **Order Tracking** (`/track/[orderId]`): Public page for buyers to download PDF/check status (referenced in "Track here: [secure link]").

### Vendor Portal (`/vendor`)
- **Login** (`/vendor/login`): Phone input -> OTP verification.
- **Dashboard** (`/vendor/dashboard`):
  - **KPI Cards**: Active Buyers, Pending Orders, Flagged Receipts, Completed Orders.
  - **Real-time Feed**: "New order from..."
  - **Orders Table**: List of orders with status badges.
- **Negotiation/Order Detail** (`/vendor/orders/[id]`):
  - **Chat Interface**: Mimics the WhatsApp/IG conversation.
  - **Action Bar**: "Send Payment Details", "Request Receipt", "Confirm Price".
  - **Receipt Viewer**: S3 Image preview, Metadata (Amount, Timestamp), Approve/Flag buttons.
  - **Textract Overlay**: If OCR is enabled, show extracted data vs. claimed data.

### CEO Portal (`/ceo`)
- **Auth**:
  - **Signup** (`/ceo/signup`): Name, Phone, Email -> OTP.
  - **Login** (`/ceo/login`): Phone -> OTP.
- **Dashboard** (`/ceo/dashboard`):
  - **KPI Cards**: Total Vendors, Flagged Vendors, Transactions, Flag Rate.
  - **Escalation Feed**: High-value transaction alerts.
- **Vendor Management** (`/ceo/vendors`):
  - **List View**: Table of vendors (Name, Phone, Status).
  - **Add Vendor Modal**: Form to onboard new vendors.
  - **Self-Assign**: Button to "Assign Self as Vendor".
- **Escalations** (`/ceo/escalations`):
  - **Approval Modal**: Detailed view of high-value receipts requiring CEO OTP.
- **Analytics** (`/ceo/analytics`):
  - **Charts**: Fraud Flags Over Time, Vendor Risk Score (Heatmap).
  - **Audit Logs**: Table with Export CSV button.
- **Settings** (`/ceo/settings`):
  - **Meta Connect**: "Connect WhatsApp" / "Connect Instagram" buttons (OAuth flow).
  - **Chatbot Config**: Greeting text, Tone dropdown, Business Hours, Live Preview.
  - **Profile**: Edit Name/Phone/Email (triggers OTP re-auth).

---

## 4. Key UI Components (shadcn/ui)

- **Data Display**: `Table`, `Card`, `Badge`, `Avatar`.
- **Feedback**: `Toast` (notifications), `Alert`, `Progress`.
- **Overlays**: `Dialog` (Modals for Escalations/OTP), `Sheet` (Mobile menu).
- **Inputs**: `Input`, `Button`, `Select`, `Switch` (Toggles), `Textarea`.
- **Navigation**: `Sidebar`, `Tabs`, `Breadcrumb`.

## 5. Critical Flows & UX Details

### The "Zero Trust" Verification UI
- **Receipt Viewer**: Needs to clearly show the *Claimed Amount* vs. *OCR Extracted Amount* (if available) vs. *Manual Check*.
- **OTP Modals**: Critical for "Step-up Authentication".
  - Used in: Login, High-Value Approval, Profile Changes.
  - UX: 6-digit input with auto-focus and countdown timer.

### The Negotiation Interface
- Needs to look like a chat application.
- Messages from "Bot", "Buyer", and "Vendor".
- System messages (e.g., "Payment Details Sent") should be distinct from chat text.

### Meta OAuth Integration
- **Settings Page**: Visual indicators for connection status (Green checkmark "Connected as +234...").
- **OAuth Callback Page**: A dedicated route (`/ceo/oauth/callback`) to handle the redirect, exchange code for token, and close the window/redirect back.

## 6. Implementation Phases

1.  **Scaffolding**: Setup Next.js, Tailwind, shadcn/ui.
2.  **Auth & Layouts**: Implement Login screens and Dashboard shells (Sidebar/Header).
3.  **Vendor Features**: Dashboard, Orders Table, Negotiation View.
4.  **CEO Features**: Dashboard, Vendor Mgmt, Analytics.
5.  **Advanced Features**: Meta OAuth UI, Chatbot Config, PDF Tracking Page.
6.  **Integration**: Connect to existing FastAPI backend.

