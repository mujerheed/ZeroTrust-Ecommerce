# TrustGuard: Zero Trust E-commerce System 

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
|-----------|---------|-----------|
| backend/ | **Core Business Logic**: Python code for Lambda functions, handling API requests, and data access. | requirements.txt, app.py (Lambda handler), auth_service.py |
| frontend/ | **User Interfaces**: React components for the Vendor and CEO Dashboards. | src/App.jsx, src/components/VendorDashboard.jsx |
| infrastructure/ | **AWS IaC**: Definitions for all cloud resources required for deployment. | trustguard-template.yaml (SAM/CloudFormation), samconfig.toml |
| docs/ | **Project Documentation**: Reports, security analyses, and architectural diagrams. | PHASE_1_PLAN.md, SECURITY_MODEL.md |