# 📚 TrustGuard Documentation

This folder contains all technical documentation for the TrustGuard Zero Trust E-Commerce system.

## 📖 Documentation Index

### **Core Documentation**

| Document | Description |
|----------|-------------|
| [PROJECT_PROPOSAL.md](./PROJECT_PROPOSAL.md) | Original project proposal and requirements |
| [README.md](./README.md) | Main documentation overview |
| [META_INTEGRATION_SETUP.md](./META_INTEGRATION_SETUP.md) | WhatsApp & Instagram integration guide |

### **Testing & Development**

| Document | Description |
|----------|-------------|
| [TEST_NOTIFICATIONS.md](./TEST_NOTIFICATIONS.md) | Guide for testing the real-time notification system |
| [test-notifications.html](./test-notifications.html) | HTML tool for creating test notifications |

---

## 🏗️ Architecture Overview

```
TrustGuard/
├── backend/              # FastAPI serverless backend
│   ├── auth_service/    # OTP authentication (Buyer/Vendor/CEO)
│   ├── vendor_service/  # Vendor dashboard & receipt verification
│   ├── ceo_service/     # CEO admin portal & approvals
│   ├── order_service/   # Order management
│   ├── receipt_service/ # S3 receipt upload & Textract OCR
│   ├── common/          # Shared utilities (config, DB, security)
│   └── integrations/    # WhatsApp/Instagram webhooks
│
├── frontend/            # Next.js 14 CEO Portal
│   ├── app/ceo/        # CEO dashboard pages
│   ├── components/     # Reusable UI components
│   └── lib/            # API client & utilities
│
└── infrastructure/      # AWS SAM deployment
    └── cloudformation/  # DynamoDB, Lambda, S3, Secrets Manager
```

---

## 🚀 Quick Start

### **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or ./venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### **Access Points**
- **Backend API**: http://localhost:8000
- **CEO Portal**: http://localhost:3000/ceo/login
- **API Docs**: http://localhost:8000/docs

---

## 📱 Features Implemented

### ✅ **CEO Portal (100% Complete)**
- Dashboard with KPIs and charts
- Vendor management (onboard, list, remove)
- Order approvals (high-value & flagged transactions)
- Analytics page (vendor performance, fraud insights)
- Audit logs (immutable security logs)
- Settings (profile, business info, chatbot config)
- Meta integrations (WhatsApp/Instagram OAuth)
- Real-time notifications with auto-pop modal
- Full dark/light mode support

### ✅ **Authentication (Zero Trust)**
- Sessionless OTP authentication (6-8 char, single-use, 5-min TTL)
- Role-based access (Buyer, Vendor, CEO)
- JWT tokens with role validation
- Multi-CEO tenancy support

### ✅ **Receipt Verification**
- S3 encrypted storage (SSE-KMS)
- Textract OCR extraction (optional)
- Manual vendor review
- Amount mismatch detection
- High-value escalation (≥ ₦1M)

### ✅ **Real-time Notifications**
- In-app notifications with metadata
- Auto-pop escalation modal
- 30-second polling
- Mark as read functionality
- Toast notifications

### ✅ **Analytics & Reporting**
- Vendor performance metrics
- Fraud detection insights
- CSV/PDF export
- Weekly trend analysis

---

## 🔐 Security Features

- **Zero Trust Architecture**: No passwords, OTP-only auth
- **Encrypted Storage**: S3 SSE-KMS, DynamoDB encryption at rest
- **PII Masking**: Sensitive data masked in logs
- **Audit Logging**: Immutable logs for all privileged actions
- **Multi-tenancy**: CEO data isolation via `ceo_id` filtering
- **Rate Limiting**: In-memory rate limits on auth endpoints
- **Webhook Security**: HMAC signature validation (Meta webhooks)

---

## 🧪 Testing

### **Test Notification System**
See [TEST_NOTIFICATIONS.md](./TEST_NOTIFICATIONS.md) for detailed guide.

**Quick Test:**
```javascript
// In browser console (CEO portal)
const token = localStorage.getItem('token');
fetch('http://localhost:8000/ceo/test/create-notification?notification_type=escalation', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
}).then(res => res.json()).then(console.log);
```

### **Backend Tests**
```bash
cd backend
pytest -v
```

---

## 📊 Database Schema

### **DynamoDB Tables**
- `TrustGuard-Users` - Buyers, Vendors, CEOs
- `TrustGuard-OTPs` - One-time passwords (with TTL)
- `TrustGuard-Orders` - Order records
- `TrustGuard-Receipts` - Receipt metadata
- `TrustGuard-AuditLogs` - Immutable security logs
- `TrustGuard-Escalations` - High-value transaction approvals
- `TrustGuard-CEOConfig` - CEO business settings
- `TrustGuard-Negotiations` - Price negotiation history

### **S3 Buckets**
- `trustguard-receipts` - Encrypted receipt images

### **Secrets Manager**
- `TrustGuard-JWTSecret` - JWT signing key
- `TrustGuard-MetaTokens-{ceo_id}` - OAuth tokens per CEO

---

## 🚧 Pending Features

- [ ] Receipt preview in Approvals page (S3 pre-signed URLs)
- [ ] Notification preferences in Settings
- [ ] Multi-tenancy testing (data isolation verification)
- [ ] Textract OCR pipeline (Lambda trigger on S3 upload)
- [ ] SMS/Email notifications via SNS

---

## 📞 Support

For questions or issues:
1. Check [PROJECT_PROPOSAL.md](./PROJECT_PROPOSAL.md) for requirements
2. Review [META_INTEGRATION_SETUP.md](./META_INTEGRATION_SETUP.md) for integration setup
3. Use [test-notifications.html](./test-notifications.html) for testing

---

## 📝 License

This project is part of the Shobhit University Minor Project.

**Last Updated**: November 22, 2025
