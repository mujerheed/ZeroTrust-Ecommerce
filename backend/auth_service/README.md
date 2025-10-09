# Authentication Service (auth_service)

This module manages user registration, login, and OTP verification to secure access.

## Structure

- `auth_routes.py`: API endpoints for registration, login, and OTP verification.
- `auth_logic.py`: Core authentication business rules.
- `otp_manager.py`: OTP generation, delivery, and verification.
- `token_manager.py`: JWT token creation and decoding.
- `database.py`: User data persistence.
- `utils.py`: Helper functions.
- `tests/`: Unit tests for authentication workflows.

## Setup

1. Install dependencies from `requirements.txt`.
2. Configure environment variables for OTP delivery and JWT secret.
3. Run tests with your preferred Python test runner.

## Usage

Calls to `/auth/register`, `/auth/login`, and `/auth/verify-otp` endpoints handle all authentication flows.

