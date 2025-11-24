# 🛡️ TrustGuard: Zero Trust E-Commerce Security System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

> **Zero Trust security platform for informal e-commerce in Nigeria**  
> Securing WhatsApp & Instagram transactions with OTP authentication, encrypted receipt storage, and real-time fraud detection.

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- AWS Account (for deployment)

### **Local Development**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Access:**
- Backend API: http://localhost:8000
- CEO Portal: http://localhost:3000/ceo/login
- API Docs: http://localhost:8000/docs

---

## 🎯 Problem & Solution

### **The Problem**
Nigeria's informal e-commerce relies on WhatsApp/Instagram for transactions, leading to:
- ❌ **Forged bank receipts** (screenshots easily faked)
- ❌ **Buyer-vendor mistrust** (no third-party verification)
- ❌ **Unprotected customer data** (PII stored insecurely)

### **The Solution**
TrustGuard implements **Zero Trust principles**:
- ✅ **Sessionless OTP authentication** (no passwords)
- ✅ **Encrypted receipt storage** (S3 with SSE-KMS)
- ✅ **Role-based dashboards** (Buyer/Vendor/CEO isolation)
- ✅ **Immutable audit logging** (full traceability)
- ✅ **Real-time fraud alerts** (auto-pop escalation modals)

---

## ✨ Key Features

### **CEO Portal** (Admin Dashboard)
- 📊 Dashboard with KPIs and charts
- 👥 Vendor management (onboard, list, remove)
- ✅ Order approvals (high-value ≥ ₦1M transactions)
- � Analytics (vendor performance, fraud insights)
- 🔔 Real-time notifications with auto-pop alerts
- 🌓 Full dark/light mode support
- 📄 CSV/PDF export

### **Authentication** (Zero Trust)
- 🔐 OTP-only (no passwords)
- ⏱️ Single-use, 5-minute TTL
- 👤 Role-based (Buyer, Vendor, CEO)
- 🔑 JWT tokens with role validation

### **Receipt Verification**
- 🖼️ S3 encrypted storage
- 🤖 Optional Textract OCR
- 💰 Amount mismatch detection
- 🚨 Auto-escalation for high-value orders

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  WhatsApp/IG    │      │   CEO Portal    │      │   Vendor Web    │
│     (Buyer)     │      │   (Next.js 14)  │      │   (React.js)    │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │   FastAPI Backend       │
                     │   (Python 3.11)         │
                     └────────────┬────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
    ┌────▼────┐            ┌──────▼──────┐         ┌──────▼──────┐
    │DynamoDB │            │  S3 Bucket  │         │   SNS/SES   │
    │ Tables  │            │  (Receipts) │         │  (Alerts)   │
    └─────────┘            └─────────────┘         └─────────────┘
```

**Services:**
- `auth_service` - OTP authentication
- `vendor_service` - Vendor dashboard & receipt verification
- `ceo_service` - CEO admin portal & approvals
- `order_service` - Order management
- `receipt_service` - S3 upload & Textract OCR
- `integrations` - WhatsApp/Instagram webhooks

---

## 📚 Documentation

- **[Full Documentation →](./docs/INDEX.md)**
- **[Project Proposal →](./docs/PROJECT_PROPOSAL.md)**
- **[Testing Guide →](./docs/TEST_NOTIFICATIONS.md)**
- **[Meta Integration →](./docs/META_INTEGRATION_SETUP.md)**

---

## 🔐 Security

**Zero Trust Pillars:**
- ✅ **Verify Explicitly** - Fresh OTP for every access
- ✅ **Least Privilege** - Scoped IAM policies, RBAC
- ✅ **Assume Breach** - Encrypted storage, immutable audit logs

**Features:**
- No passwords (OTP-only)
- PII masking in logs
- HMAC webhook validation
- Rate limiting
- Multi-CEO tenancy isolation

---

## 🧪 Testing

**Test Notification System:**
```javascript
// Browser console (CEO portal)
const token = localStorage.getItem('token');
fetch('http://localhost:8000/ceo/test/create-notification?notification_type=escalation', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

See [docs/TEST_NOTIFICATIONS.md](./docs/TEST_NOTIFICATIONS.md) for detailed guide.

---

## � Deployment

```bash
cd infrastructure/cloudformation
sam build
sam deploy --guided
```

**AWS Resources:**
- 5 DynamoDB tables (encrypted at rest)
- S3 bucket (SSE-KMS encryption)
- 4 Lambda functions
- Secrets Manager (JWT secret, OAuth tokens)
- SNS topics (alerts)

---

## 📝 License

This project is part of the **Shobhit University Minor Project** (3rd Semester).

**Team**: [Your Name]  
**Supervisor**: [Supervisor Name]  
**Year**: 2025

---

## 🤝 Contributing

This is an academic project. For questions or suggestions, please contact the project team.

---

**Last Updated**: November 22, 2025
│   │   ├── token_manager.py            # JWT handling
│   │   ├── database.py                 # Auth data persistence
│   │   ├── utils.py                    # Helper utilities (formatting, validators)
│   │   └── tests/
│   │       └── test_auth.py            # Unit tests
│
│   ├── ceo_service/                    # Module 2 - CEO Dashboard & Admin Controls
│   │   ├── __init__.py
│   │   ├── ceo_routes.py               # API endpoints for CEO
│   │   ├── ceo_logic.py                # CEO business logic
│   │   ├── vendor_manager.py           # Manage vendor accounts
│   │   ├── audit_log_manager.py        # Audit log handling
│   │   ├── approval_manager.py         # Transaction approvals, escalation
│   │   ├── database.py                 # CEO data persistence
│   │   ├── utils.py                    # Helper utilities
│   │   └── tests/
│   │       ├── test_ceo.py
│   │       ├── test_approval.py
│   │       └── test_audit_log.py
│
│   ├── vendor_service/                 # Module 3 - Vendor Dashboard & Transactions
│   │   ├── __init__.py
│   │   ├── vendor_routes.py            # Vendor API endpoints
│   │   ├── vendor_logic.py             # Vendor business logic
│   │   ├── transaction_manager.py     # Transaction handling & OTP validation
│   │   ├── database.py                 # Vendor data persistence
│   │   ├── utils.py                    # Helper utilities
│   │   └── tests/
│   │       └── test_vendor.py
│
│   ├── integrations/                  # External integrations and webhook handlers
│   │   ├── __init__.py
│   │   ├── whatsapp_api.py             # WhatsApp Business API integration
│   │   ├── instagram_api.py            # Instagram Messaging API integration
│   │   ├── sms_gateway.py              # SMS gateway (fallback)
│   │   └── webhook_handler.py          # Incoming message webhook handler
│
│   ├── common/                       # Shared utilities and configurations
│   │   ├── __init__.py
│   │   ├── db_connection.py           # DB setup/config
│   │   ├── config.py                  # Environment/configuration constants
│   │   ├── logger.py                  # Central logging facility
│   │   └── security.py                # Encryption, hashing, etc.
│
├── frontend/                          # Web frontends (optional or later phase)
│   ├── index.html
│   ├── dashboard.html
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── api_client.js                  # JS code calling backend endpoints
│
├── docs/                             # Project documentation
│   ├── ArchitectureDiagram.png
│   ├── Flowchart.png
│   ├── API_Documentation.md
│   └── DeveloperGuide.md
│
├── .gitignore
└── README.md                        # Repository-wide overview

## Project Modules

- `auth_service`: Handles user registration, login, and OTP authentication.
- `ceo_service`: CEO dashboard for managing vendors, approving transactions, and monitoring audit logs.
- `vendor_service`: Vendor dashboard for order management, receipt verification, and transaction approvals.
- `integrations`: WhatsApp, Instagram, and SMS gateway APIs.
- `common`: Shared configurations, database connections, and utilities.

## Setup Instructions

1. Clone the repository.
2. Follow individual module README files for detailed setup.
3. Configure your environment variables and API credentials as per `.env.example`.
4. Deploy infrastructure using scripts in the `infrastructure/` folder.
5. Run backend and optionally frontend components.

## Contribution

Please refer to each module's README for contribution guidelines.