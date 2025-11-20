# 🎨 TrustGuard Frontend Development Plan

**Status**: Planning Phase  
**Backend**: ✅ 100% Complete & Deployed  
**Goal**: Build a modern, responsive web interface for CEOs and Vendors.

---

## 🛠️ Technology Stack

- **Framework**: [Next.js 14](https://nextjs.org/) (App Router)
- **Language**: TypeScript
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Components**: [shadcn/ui](https://ui.shadcn.com/) (Radix UI + Tailwind)
- **State Management**: [TanStack Query](https://tanstack.com/query/latest) (React Query)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Forms**: React Hook Form + Zod
- **PDF Viewer**: react-pdf (optional) or native browser viewer

---

## 📱 Core Portals

### 1. Authentication (Public)
- **CEO Login**: Email + OTP flow (`/auth/ceo/login`)
- **Vendor Login**: Email + OTP flow (`/auth/vendor/login`)
- **Logout**: Clear tokens

### 2. CEO Dashboard (Admin)
- **Overview**:
  - Key metrics (Total Volume, Fraud Rate, Active Vendors)
  - Fraud trends chart
- **Approvals Center**:
  - List of high-value orders (≥ ₦1M) or flagged receipts
  - Approve/Reject actions with OTP verification
- **Vendor Management**:
  - List all vendors
  - Add new vendor (Modal)
  - Deactivate/Delete vendor
- **Audit Logs**:
  - Immutable log viewer (who did what, when)
- **Settings**:
  - **Bank Details**: Update account info for payments
  - **Chatbot**: Configure greeting, catalog, auto-replies
  - **Meta Integration**: Connect WhatsApp/Instagram

### 3. Vendor Dashboard (Operations)
- **Overview**:
  - Daily order stats
  - Pending verifications count
- **Order Management**:
  - List orders (Filter by status: Pending, Paid, Delivered)
  - Search orders (Buyer name, ID, Phone)
- **Order Details**:
  - View items, totals, delivery address
  - **Action**: Verify Receipt (View Image/PDF, Approve/Flag)
  - **Action**: Download PDF Invoice
  - **Action**: Update Delivery Status

---

## 🗓️ Implementation Phases

### Phase 1: Setup & Authentication (Week 1)
- Initialize Next.js project
- Configure Tailwind & shadcn/ui
- Setup API client (Axios + Interceptors for JWT)
- Implement Login screens (CEO & Vendor)
- OTP Input components

### Phase 2: CEO Dashboard (Weeks 2-3)
- Dashboard Layout (Sidebar, Header)
- Vendor Management CRUD
- Approval Workflow (High-value transactions)
- Settings pages (Bank details, Chatbot)

### Phase 3: Vendor Dashboard (Weeks 4-5)
- Order List with filters
- Order Detail view
- Receipt Verification interface (Image zoom, PDF viewer)
- PDF Download integration

### Phase 4: Polish & Deployment (Week 6)
- Error handling & Loading states
- Responsive design testing (Mobile support)
- Deployment to Vercel or AWS Amplify
- End-to-end testing

---

## 🔌 API Integration Points

| Feature | Backend Endpoint | Method |
|---------|------------------|--------|
| **Auth** | `/auth/ceo/login`, `/auth/vendor/login` | POST |
| **CEO Stats** | `/ceo/dashboard`, `/ceo/analytics/*` | GET |
| **Approvals** | `/ceo/approvals`, `/ceo/approvals/{id}/*` | GET/PATCH |
| **Vendors** | `/ceo/vendors` | GET/POST/DEL |
| **Orders** | `/vendor/orders`, `/vendor/orders/{id}` | GET |
| **Receipts** | `/vendor/receipts/{id}`, `/vendor/orders/{id}/verify` | GET/POST |
| **PDF** | `/orders/{id}/download-pdf` | GET |

---

## 🚀 Getting Started

```bash
# 1. Create Project
npx create-next-app@latest frontend --typescript --tailwind --eslint

# 2. Install Dependencies
npm install lucide-react axios @tanstack/react-query class-variance-authority clsx tailwind-merge
npm install -D @types/node @types/react @types/react-dom

# 3. Initialize shadcn/ui
npx shadcn-ui@latest init
```
