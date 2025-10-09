# TrustGuard: Zero Trust E-commerce System 
---

## 🛡️ Project Overview
This repository contains the implementation of TrustGuard, a state-of-the-art Zero Trust Security System designed to secure informal e-commerce transactions conducted over social media platforms (primarily WhatsApp and Instagram) in Nigeria. The system directly addresses critical security gaps in current workflows, ensuring that no user (buyer, vendor, or administrator) is implicitly trusted.

### Core Problems Addressed (Context: Nigeria's Informal E-commerce)
1. **Forged Receipts**: Transactions rely on easy-to-manipulate bank transfer screenshots.
2. **Buyer-Vendor Mistrust**: Lack of a secure, third-party verification layer for identity and payment.
3. **Lack of Structured Access Control**: Vendors and administrators often operate without role separation, leading to data risks.
4. **Unprotected Customer Data**: Sensitive PII is collected and stored insecurely.

### Key Project Objectives
- Implement **OTP-based, single-use authentication** for Buyers, Vendors, and CEOs.
- Establish a **secure, encrypted pipeline** for uploading, storing, and accessing payment receipts (Proof of Payment).
- Enforce **Role-Based Access Control (RBAC)** via dedicated Vendor and CEO dashboards.
- Ensure full **traceability and non-repudiation** through immutable, detailed Audit Logging of every critical action.
- Provide a scalable, serverless architecture ready for future enhancements (e.g., AI-based fraud detection).

## 🔑 Zero Trust Pillars Implemented
| Pillar | Implementation in TrustGuard | Security Benefit |
|--------|------------------------------|------------------|
| __Verify Explicitly__ | All access, regardless of location (Buyer via WhatsApp, Vendor via Web), requires fresh, time-limited OTP authentication. | Eliminates implicit trust based on network or location. |
| __Use Least Privilege__ | AWS IAM Policies are scoped narrowly for each Lambda function. Vendor and CEO dashboards only display data relevant to their role (RBAC). | Minimizes the blast radius of a potential breach. |
| __Assume Breach__ | All data (DynamoDB, S3 receipts) is encrypted at rest. Comprehensive AuditLogs track every user and system event. | Ensures data protection even if systems are compromised and provides forensic evidence. |

## ⚙️ Technology Stack
| Layer | Service/Framework | Purpose |
|-------|-------------------|---------|
| __Backend (Severless)__ | AWS Lambda (Python 3.11) | Hosts all core business logic (Auth, OTP, Auditing, S3 management). |
| __Data Storage__ | AWS DynamoDB | Highly available, encrypted storage for Users (Buyers, Vendors, CEOs), OTPs, and AuditLogs. |
| __Secure File Storage__ | AWS S3 (Encrypted) | Stores payment receipt images with enforced server-side encryption. |
| __Infrastructure__ | AWS Serverless Application Model (SAM) | Infrastructure as Code (IaC) for defining and deploying all AWS resources securely. |
| __Integration__ | AWS SNS/SES + Messaging APIs | OTP delivery via SMS/Email/WhatsApp/Instagram DMs. |
| __Frontend/Dashboards__ | React.js | Vendor and CEO web interfaces with authenticated, role-based views. |

## 📁 Project Structure
| Directory | Purpose | Key Files |
ZeroTrust-Ecommerce/
│
├── backend/                              # Backend logic root
│   ├── app.py                          # Central router (entry point)
│   ├── requirements.txt                # Python dependencies
│   ├── README.md                      # Backend project overview and setup
│
│   ├── auth_service/                   # Module 1 - Authentication & OTP
│   │   ├── __init__.py
│   │   ├── auth_routes.py              # API endpoints (/auth/register, /login, /verify-otp)
│   │   ├── auth_logic.py               # Core auth logic
│   │   ├── otp_manager.py              # OTP generation, sending, verification
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