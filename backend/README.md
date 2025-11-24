# TrustGuard Backend

This is the backend for the TrustGuard Zero Trust E-commerce platform. It is a modular serverless application built with FastAPI and AWS SAM.

## Structure

The backend is divided into three main services and a shared common library:

### 1. Authentication Service (`auth_service/`)
Manages user registration, login, and OTP verification to secure access.
- `auth_routes.py`: API endpoints for registration, login, and OTP verification.
- `auth_logic.py`: Core authentication business rules.
- `otp_manager.py`: OTP generation, delivery (SMS/Email), and verification.
- `token_manager.py`: JWT token creation and decoding.
- `database.py`: User data persistence.

### 2. CEO Service (`ceo_service/`)
Serves the CEO dashboard and admin APIs, facilitating vendor management, transaction approvals, and audit log monitoring.
- `ceo_routes.py`: CEO-specific API endpoints.
- `ceo_logic.py`: Business logic for admin actions.
- `database.py`: Persistence layer for CEO data.

### 3. Vendor Service (`vendor_service/`)
Provides APIs and logic for the vendor dashboard including order management and receipt verification.
- `vendor_routes.py`: API endpoints for vendor operations.
- `vendor_logic.py`: Vendor-specific business logic.
- `database.py`: Vendor data storage.

### 4. Integrations (`integrations/`)
Handles external communication with WhatsApp Business API, Instagram Messaging API, SMS gateway, and incoming webhook handlers.

### 5. Common (`common/`)
Shared utilities and configuration.
- `config.py`: Environment configuration.
- `db_connection.py`: AWS client initialization (DynamoDB, S3, SNS, SES).
- `logger.py`: Structured logging.
- `security.py`: Security helpers.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Configuration**:
    - Ensure `.env` file is configured with correct AWS region and DynamoDB table names.
    - For local development, use `uvicorn app:app --reload`.

3.  **Testing**:
    - Unit tests are located in `tests/` within each service directory.
    - E2E tests are located in `tests/e2e/`.
    - Run tests with `pytest`.
