# CEO Service (ceo_service)

Serves the CEO dashboard and admin APIs, facilitating vendor management, transaction approvals, and audit log monitoring.

## Structure

- `ceo_routes.py`: CEO-specific API endpoints.
- `ceo_logic.py`: Business logic for admin actions.
- `vendor_manager.py`: Manage vendor lifecycle.
- `approval_manager.py`: Handles escalated transaction approvals.
- `audit_log_manager.py`: Audit log querying and management.
- `database.py`: Persistence layer for CEO data.
- `utils.py`: Helper functions.
- `tests/`: Unit and integration tests for CFO workflows.

## Setup

1. Install dependencies as per backend `requirements.txt`.
2. Configure API credentials and logging.
3. Run tests located in the `tests/` folder.

## Usage

Use CEO endpoints for managing vendors, reviewing flagged transactions, and accessing audit logs.

