# TrustGuard: Zero Trust Security System for Informal E-commerce in Nigeria

## 1. Introduction
Informal e-commerce in Nigeria thrives through platforms like WhatsApp, Instagram, and Facebook rather than traditional online stores. These decentralized channels lack verification, authentication, and reliable payment validation.

**Current issues include:**
- Buyers and vendors operate on mutual trust without technical proof of authenticity.
- Bank receipts are manually verified and can easily be forged.
- Customer data and chat histories are exchanged insecurely.
- No standardized access control between buyers, vendors, and administrators.

**Objective:**  
Develop a **Zero Trust–based security architecture** that verifies all entities, encrypts sensitive data, and ensures every action is authenticated and auditable across the entire informal e-commerce workflow.

---

## 2. Problem Statement
The informal e-commerce model in Nigeria is vulnerable because it depends on **manual trust**, not **verifiable security**.  
Key weaknesses:
- Lack of pre-transaction verification (anyone can pose as a vendor or buyer).
- Fake or altered bank receipts.
- Shared login credentials or uniform privileges among users.

**Solution Approach:**  
Adopt the **Zero Trust Architecture (ZTA)** model emphasizing:
- **Verify explicitly** — Authenticate all buyers, vendors, and admins before every sensitive action.
- **Least privilege access** — Restrict permissions to only what each role needs.
- **Assume breach** — Log, monitor, and encrypt every transaction as if the system were already compromised.

---

## 3. System Overview

### 3.1 Core Components
- **Frontend Channels**  
  - WhatsApp Business API and Instagram Messaging API for customer-facing interaction.
- **Backend (AWS)**  
  - API Gateway as the entry point for all requests.  
  - AWS Lambda functions for modular microservices:
    - `AuthService` – Handles OTP generation and verification.
    - `ReceiptService` – Manages receipt uploads and validation.
    - `VendorService` – Handles vendor/CEO dashboards.
  - DynamoDB for encrypted, serverless data storage.
  - S3 for secure receipt storage (AES256 encryption).

### 3.2 Security Architecture
- Every OTP request, verification, and transaction is logged in **AuditLogs (DynamoDB)**.  
- **JWT tokens** provide temporary access authorization.  
- The **Principle of Least Privilege** is enforced through IAM roles in the SAM template.  
- All data-at-rest and in-transit are encrypted.  

### 3.3 Zero Trust Layers
1. **Identity Verification** – OTP validation before any sensitive transaction.
2. **Access Control** – Dynamic role-based permissions (Buyer, Vendor, CEO).
3. **Audit Logging** – Immutable logs for compliance and forensic review.
4. **Encryption** – AES256 for S3, AWS KMS for DynamoDB encryption keys.
5. **Microservice Isolation** – Separate Lambda functions for each business logic path.

---

## 4. Workflow Summary

### 4.1 Buyer Flow
1. Buyer initiates chat via WhatsApp or Instagram.  
2. The bot collects name, phone, and delivery details.  
3. OTP is sent for identity verification.  
4. Upon successful verification, order data is logged.  

### 4.2 Vendor Flow
1. Vendors log in via secure dashboard (JWT-authenticated).  
2. Vendors access only their sales and delivery data.  
3. Every action (update, view, upload) is logged to `AuditLogs`.  

### 4.3 CEO Flow
1. CEO oversees all vendors and transaction logs.  
2. Only CEO has authority to override or approve vendor-level changes.  
3. High-privilege operations (approvals, payments) use 2FA-style OTP.  

---

## 5. AWS Infrastructure Overview

| Component | Service | Purpose |
|------------|----------|----------|
| API Gateway | AWS API Gateway | Routes external requests to the right Lambda service |
| Authentication | AWS Lambda (AuthService) | OTP request and verification |
| Data Layer | DynamoDB | User data, OTPs, and audit logs |
| File Storage | S3 Bucket | Encrypted receipt storage |
| Logging | CloudWatch + DynamoDB | Forensics and accountability |

### CloudFormation/SAM Template Reference
File: `trustguard-template.yaml`  
Defines all resources including:
- DynamoDB Tables (`TrustGuard-Users`, `TrustGuard-OTPs`, `TrustGuard-AuditLogs`)
- S3 Bucket for receipts
- Three Lambda microservices with least-privilege IAM roles

---

## 6. Expected Impact

**1. Increased Trust:**  
Vendors and buyers transact with cryptographic verification.  

**2. Fraud Reduction:**  
Receipt forgery and impersonation are minimized through verifiable logs and OTP-bound actions.  

**3. Accountability:**  
Every step — from message to payment confirmation — leaves an immutable audit record.  

**4. Regulatory Compliance:**  
The design aligns with data protection principles and Zero Trust frameworks recognized by NIST.

---

## 7. Technology Stack

| Layer | Technology |
|--------|-------------|
| Cloud Provider | AWS |
| Backend | Python (AWS Lambda) |
| Databases | DynamoDB |
| File Storage | AWS S3 |
| APIs | WhatsApp Business API, Instagram Graph API |
| Security | Zero Trust (Least Privilege, Assume Breach, Verify Explicitly) |
| Authentication | JWT, OTP (custom logic) |
| Monitoring | AWS CloudWatch |

---

## 8. Future Work
- Integrate **receipt forgery detection** using ML-based image analysis.
- Develop **vendor dashboard frontend** using React or Next.js.
- Implement **chat-based AI assistant** for vendor–buyer support.
- Extend integrations to **SMS and email fallback** when messaging APIs fail.

---

## 9. Conclusion
TrustGuard bridges informal social commerce and enterprise-level Zero Trust security.  
It transforms unverified WhatsApp and Instagram transactions into **secure, verified, and logged digital processes** while preserving simplicity and accessibility.

By enforcing verification at every layer, the system ensures that **no action, user, or device is trusted by default**, creating a secure informal e-commerce network for Nigeria’s growing digital market.

---

### Appendix A — File Structure Reference

ZeroTrust-Ecommerce/
├── backend/
│ ├── app.py
│ ├── auth_service.py
│ ├── requirements.txt
│ ├── trustguard-template.yaml
│ └── ...
├── docs/
│ └── PROJECT_PROPOSAL.md
├── frontend/
│ └── (future React dashboard)
└── .gitignore