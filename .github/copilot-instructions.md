# TrustGuard AI Agent Instructions

This guide enables AI coding agents to be immediately productive in the TrustGuard (ZeroTrust-Ecommerce) repo. It covers architecture, workflows, conventions, and integration points unique to this project.
## System Overview

TrustGuard is a Zero Trust security platform for informal e-commerce (Nigeria focus). It secures buyer-vendor interactions on WhatsApp/Instagram, prevents forged receipts, and protects PII. Key actors: Buyer (chat/receipt upload), Vendor (dashboard/order/receipt review), CEO (admin, onboarding, approvals).
## Quick Start & Entrypoints

- Main FastAPI app: `backend/app.py`
  - Local run: `pip install -r backend/requirements.txt && uvicorn backend.app:app --reload --port 8000`
## Architecture & Data Flow

- Modular backend: `auth_service/`, `vendor_service/`, `ceo_service/` (each has routes, logic, database helpers)
...
## Repo Conventions & Patterns

- API responses: always use `format_response(status, message, data)` (see `*_service/utils.py`)
...
## Patterns & Gotchas

- Two rate-limit helpers: `backend/common/security.rate_limit` (FastAPI Request) and `rate_limit_check` (signature varies, not always present)
...
## Developer Workflows

- Unit tests: `backend/*/tests/` (run: `cd backend && pytest -q`)
...
## Deployment & Infra

- AWS SAM: see `infrastructure/cloudformation/trustguard-template.yaml`, deploy with `infrastructure/scripts/deploy.sh`
...
## Key Files & Examples

- Add/modify endpoint: `backend/*_service/*_routes.py`, `*_logic.py`, `database.py`
...
## Before Large Changes, Always Ask:

- Target environment: local, AWS dev, or CI?
...
## Purpose

This file gives an AI coding agent exactly what it needs to be productive in the TrustGuard (ZeroTrust-Ecommerce) repo: the high-level architecture, common patterns, how to run and test locally, and where to look for implementation examples.

## What This System Does (Business Context)

TrustGuard is a **Zero Trust security system for informal e-commerce in Nigeria**. Vendors conduct business via WhatsApp/Instagram (not dedicated e-commerce sites). The system addresses:
- **Forged bank receipts** (screenshots are easily faked)
- **Buyer-vendor mistrust** (no third-party verification)
- **Unprotected customer data** (PII stored insecurely)

Key actors:
- **Buyers**: discover products on Instagram/WhatsApp, authenticate via OTP in chat, upload payment receipts
- **Vendors**: manage orders via dashboard, verify receipts, handle transactions (registered by CEO)
- **CEO**: business owner, onboards vendors, approves high-value/flagged transactions, oversees all operations via admin dashboard

The system uses **sessionless OTP authentication**, **encrypted receipt storage (S3)**, **role-based dashboards**, and **immutable audit logging** following Zero Trust principles.

## Quick orientation (entrypoints & run)

- Primary FastAPI entrypoint: `backend/app.py`. For local development run:
  - Install dependencies: `pip install -r backend/requirements.txt`
  - Start server: `uvicorn backend.app:app --reload --port 8000`
  - Note: `backend/app.py` uses `Mangum` — in AWS Lambda the handler is exposed as `handler`.
- Environment: `.env` is loaded locally (see `backend/common/config.py` which uses Pydantic `BaseSettings`). Expect required env vars: `AWS_REGION`, `USERS_TABLE`, `OTPS_TABLE`, `ORDERS_TABLE`, `RECEIPTS_TABLE`, `AUDIT_LOGS_TABLE`, `JWT_SECRET`, `RECEIPT_BUCKET`, etc.
- **Secrets Manager**: In production, `JWT_SECRET` and Meta API tokens are stored in AWS Secrets Manager (`TrustGuard-JWTSecret`), not `.env`.

## Big-picture architecture (what to know)

- **Three-service modular serverless backend** under `backend/`:
  - `auth_service/` — OTP flows for Buyer/Vendor/CEO authentication (endpoints: `auth_routes.py`, logic in `auth_logic.py`, OTP generation in `otp_manager.py`). Handles buyer registration via WhatsApp/Instagram bot webhooks.
  - `vendor_service/` — vendor dashboard, order management, receipt verification (`vendor_routes.py`, `vendor_logic.py`).
  - `ceo_service/` — CEO admin dashboard, vendor onboarding, high-value transaction approvals, audit log access (`ceo_routes.py`, `ceo_logic.py`).
- **Shared utilities and infra clients** in `backend/common/`:
  - `config.py` (Pydantic Settings), `db_connection.py` (boto3 clients for DynamoDB/S3), `security.py` (JWT helpers and in-memory rate limiter), `logger.py` (structured JSON logging via `pythonjsonlogger`).
- **Integration layer** (`backend/integrations/`):
  - **Meta Webhooks**: WhatsApp Business API and Instagram Messaging API webhooks receive buyer messages. Webhook handler validates HMAC (`X-Hub-Signature-256`) using Meta App Secret before processing.
  - **OTP delivery**: via platform DM (WhatsApp/Instagram) or SMS fallback (AWS SNS).
  - **Chatbot Router**: tags incoming messages with `ceo_id` for multi-CEO tenancy support.
  - **Mock API**: `backend/integrations/mock_api` simulates Meta payloads for local/dev testing without live tokens.
- **Data stores**:
  - **DynamoDB tables**: `TrustGuard-Users`, `TrustGuard-OTPs` (with TTL), `TrustGuard-Orders`, `TrustGuard-Receipts`, `TrustGuard-AuditLogs` (write-only for services, immutable logs).
  - **S3 bucket**: `TrustGuard-Receipts` (server-side encryption SSE-KMS, organized by `receipts/{ceo_id}/{vendor_id}/{order_id}/...`).
  - **Secrets Manager**: stores Meta OAuth tokens (long-lived, per `ceo_id`) and `JWT_SECRET`.
- **Receipt verification pipeline**:
  - Buyer uploads receipt → S3 presigned PUT URL → metadata stored in `TrustGuard-Receipts`.
  - Optional: S3 event triggers Textract OCR job → `textract_worker` Lambda writes results back to `ReceiptsMeta` with confidence scores.
  - Vendor reviews receipt (manual or OCR-assisted) → approves or flags.
  - Flagged or high-value (≥ ₦1,000,000) receipts escalate to CEO via `approval_request` record + SNS notification.
- **Multi-CEO tenancy**: buyer records, orders, and OAuth tokens are keyed by `ceo_id`; each business operates independently with isolated data.

## Key repo conventions & idioms (project-specific)

- **API response shape**: many modules use a `format_response(status, message, data)` helper (see `auth_service/utils.py`, `vendor_service/utils.py`, `ceo_service/utils.py`). Preserve this shape for consistency.
- **JWTs**: tokens encode `sub` (subject/user_id) and `role` (e.g., `Buyer`, `Vendor`, `CEO`). Helpers: `backend/common/security.create_jwt/decode_jwt` and service-level `verify_*_token` (e.g., `vendor_service/utils.verify_vendor_token`, `ceo_service/utils.verify_ceo_token`).
- **OTP formats** (role-specific, validated in `auth_service/utils.validate_otp_format`):
  - **Buyer OTP**: 8 characters (alphanumeric + special chars: `!@#$%^&*`), TTL 5 min, single-use.
  - **Vendor OTP**: 8 characters (same format as Buyer).
  - **CEO OTP**: 6 characters (digits + symbols: `0-9!@#$%^&*`), TTL 5 min, single-use.
- **Phone/email validation**: `auth_service/utils.validate_phone_number` enforces Nigerian phone formats (`+234`, `234`, or `0` prefix). Use this for all phone input.
- **PII masking**: Always mask sensitive data in logs. Use `auth_service/utils.mask_sensitive_data` or `vendor_service/utils.mask_phone_number` (shows last 4 digits only).
- **Webhook security**: All Meta webhooks must validate HMAC signature (`X-Hub-Signature-256`) using Meta App Secret before processing payloads (see `integrations/webhook_handler.py`).
- **Buyer identification**: `buyer_id` format is `<platform_prefix>_<sender_id>` (e.g., `wa_1234567890` for WhatsApp, `ig_9876543210` for Instagram).
- **High-value escalation**: transactions ≥ ₦1,000,000 or flagged receipts create `approval_request` records that require CEO OTP-verified approval.

## Important patterns & gotchas discovered

- There are two rate-limit helpers with different signatures:
  - `backend/common/security.rate_limit(request, key, limit, period_seconds)` expects a FastAPI `Request`.
  - `auth_service/auth_routes.py` calls `rate_limit_check(host, "name", max_attempts, window_minutes)` — a helper reference that is not present in `auth_service/utils.py`. Be careful: code references may be inconsistent; search before changing rate-limit behavior.
- Many endpoints assume the caller will mask or log only partial PII (e.g., phone's last 4 digits). Respect `mask_phone_number` and logging helpers in `auth_service/utils.py` and `vendor_service/utils.py`.
- The FastAPI routers are mounted with prefixes in `backend/app.py`: `/auth`, `/vendor`, `/ceo`. Use those when writing integration tests or mocks.

## Tests & developer workflows

- Unit tests exist under each service in `backend/*/tests/` (e.g., `backend/auth_service/tests/test_auth.py`). Run tests from repo root:
  - `cd backend && pytest -q` (after installing `backend/requirements.txt`).
- **Local dev flow** to iterate on endpoint logic:
  1. Start uvicorn: `uvicorn backend.app:app --reload --port 8000`.
  2. Use Postman or curl against `http://localhost:8000/auth/...`, `/vendor/...`, or `/ceo/...`.
  3. For webhook-based buyer OTPs, use the `auth_service` webhook path (`/auth/webhook/buyer-otp`) — payloads should include `buyer_id`, `otp`, and `platform`.
- **Mock API for local testing**: Use `backend/integrations/mock_api` to simulate Meta webhook payloads without live WhatsApp/Instagram tokens. Mock orders stored in `backend/mock_store.json`.
- **SAM local testing**: After SAM build, run `sam local start-api` to test Lambda handlers locally (requires Docker).

## Deployment & infra notes

- The repo uses **AWS SAM** for serverless deployments (see `infrastructure/samconfig.toml` and `infrastructure/cloudformation/trustguard-template.yaml`). Deploy helper at `infrastructure/scripts/deploy.sh`.
- **SAM template key resources**:
  - 5 DynamoDB tables: `TrustGuard-Users`, `TrustGuard-OTPs` (with TTL), `TrustGuard-Orders`, `TrustGuard-Receipts`, `TrustGuard-AuditLogs`.
  - S3 bucket: `trustguard-receipts-{AccountId}-{Region}` with SSE-AES256 encryption.
  - Secrets Manager: `TrustGuard-JWTSecret` for JWT signing key (auto-generated 32-char secret).
  - 4 Lambda functions: `AuthServiceLambda`, `ReceiptServiceLambda`, `VendorServiceLambda`, `CEOServiceLambda` — all use `backend/` as `CodeUri` and share the same handler entry point via Mangum.
- **Lambda compatibility**: handlers assume `Mangum` + Python 3.11; `app.lambda_handler` is the entry for all services (routed via API Gateway paths `/auth`, `/vendor`, `/ceo`, `/receipt`).
- **IAM scoping**: Each Lambda has scoped IAM policies (e.g., VendorService can only query `TrustGuard-Orders` via `VendorIndex` GSI, not full table scan).
- **Deploy command** (from `infrastructure/cloudformation/`):
  ```bash
  sam build
  sam deploy --guided  # first time; saves config to samconfig.toml
  ```

## File pointers for common tasks (examples)

- To add/modify an endpoint: see `backend/*_service/*_routes.py` (routes), `*_logic.py` (business logic), and `database.py` files for persistence helpers.
- To add a DB table or change settings: update `backend/common/config.py` (Pydantic settings) and the SAM template under `infrastructure/cloudformation/`.
- To change logging or add structured fields: update `backend/common/logger.py` (uses `pythonjsonlogger`).

## What the AI should ask before making large changes

- Which environment should be targeted for deployment (local Docker, AWS dev account, or CI)?
- Are we allowed to modify infra (SAM templates) or only application code? Be explicit when proposing changes that affect AWS resources (DynamoDB tables, S3 buckets, IAM policies, Secrets Manager).
- Confirm policy for missing helpers discovered (e.g., `rate_limit_check`) — should the AI implement a new helper, or adapt existing `common/security.rate_limit` usage?
- For webhook or Meta API changes: do you have live WhatsApp Business API / Instagram Messaging API credentials, or should mock/local mode be used?
- For receipt verification or Textract features: is the Textract OCR pipeline enabled for this deployment, or is it manual-only review?

---
If anything here is unclear or incomplete, tell me what area you want expanded (run commands, infra details, or specific feature wiring) and I will iterate.
