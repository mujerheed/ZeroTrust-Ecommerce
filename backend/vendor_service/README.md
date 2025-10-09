# Vendor Service (vendor_service)

Provides APIs and logic for the vendor dashboard including order management and receipt verification.

## Structure

- `vendor_routes.py`: API endpoints for vendor operations.
- `vendor_logic.py`: Vendor-specific business logic.
- `transaction_manager.py`: Manages transaction record and OTP validation.
- `database.py`: Vendor data storage.
- `utils.py`: Helper utilities.
- `tests/`: Unit tests for vendor functionalities.

## Setup

1. Install dependencies outlined in backend `requirements.txt`.
2. Configure environment variables and database connections.
3. Run tests using your test framework.

## Usage

Vendor endpoints allow viewing orders, uploading receipts, and approving transactions.

