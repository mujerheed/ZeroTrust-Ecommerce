# Common Utilities Module

**Purpose**: Shared infrastructure, security, and utility modules used across all TrustGuard services.

---

## 📁 Module Overview

This directory contains common utilities that are imported by all backend services (auth_service, vendor_service, ceo_service, integrations).

### Zero Trust Principles Applied:
- ✅ **Verify Explicitly**: JWT validation, Secrets Manager integration
- ✅ **Least Privilege**: Database connection scoping per service
- ✅ **Assume Breach**: Encrypted storage, PII masking, immutable audit logs

---

## 📦 Modules

### 1. `config.py` - Configuration Management
**Purpose**: Centralized environment variable management with AWS Secrets Manager integration.

**Key Features**:
- Pydantic-based settings validation
- AWS Secrets Manager integration (production)
- Local `.env` file support (development)
- Fresh secret fetching (no caching for Zero Trust)

**Usage**:
```python
from common.config import settings

# Access configuration
table_name = settings.USERS_TABLE
jwt_secret = settings.get_jwt_secret()  # Fetches from Secrets Manager in Lambda
meta_token = settings.get_meta_token(ceo_id="ceo_001")
```

**Environment Variables**:
```bash
# DynamoDB Tables
USERS_TABLE=TrustGuard-Users
OTPS_TABLE=TrustGuard-OTPs
ORDERS_TABLE=TrustGuard-Orders
ESCALATIONS_TABLE=TrustGuard-Escalations
CEO_MAPPING_TABLE=TrustGuard-CEOMapping
AUDIT_LOGS_TABLE=TrustGuard-AuditLogs
RECEIPTS_TABLE=TrustGuard-Receipts

# S3
RECEIPT_BUCKET=trustguard-receipts-{AccountId}-us-east-1

# SNS
ESCALATION_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:{AccountId}:TrustGuard-EscalationAlert

# Business Logic
HIGH_VALUE_THRESHOLD=1000000  # ₦1,000,000

# Secrets Manager
SECRETS_PATH_APP=/TrustGuard/dev/app
SECRETS_PATH_META=/TrustGuard/dev/meta
```

---

### 2. `db_connection.py` - AWS SDK Clients
**Purpose**: Centralized boto3 client initialization for DynamoDB, S3, SNS, Secrets Manager.

**Key Features**:
- Singleton pattern for client reuse
- Region-aware initialization
- Connection pooling for Lambda optimization

**Usage**:
```python
from common.db_connection import dynamodb, s3_client, sns_client, secrets_manager

# DynamoDB table access
table = dynamodb.Table(settings.USERS_TABLE)
response = table.get_item(Key={'user_id': 'user_001'})

# S3 operations
presigned_url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': settings.RECEIPT_BUCKET, 'Key': 'receipts/order_123.jpg'},
    ExpiresIn=300
)

# SNS notifications
sns_client.publish(
    TopicArn=settings.ESCALATION_SNS_TOPIC_ARN,
    Message='High-value transaction detected'
)

# Secrets Manager
secret = secrets_manager.get_secret_value(SecretId='/TrustGuard/dev/app')
```

---

### 3. `security.py` - Security Utilities
**Purpose**: JWT helpers, rate limiting, input validation, PII masking.

**Key Features**:
- JWT creation and validation (HS256)
- In-memory rate limiting (IP-based)
- Input sanitization
- PII masking for logs

**Usage**:
```python
from common.security import create_jwt, decode_jwt, rate_limit

# Create JWT
token = create_jwt(user_id="vendor_001", role="Vendor", ceo_id="ceo_123")
# Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Validate JWT
payload = decode_jwt(token)
# Returns: {'sub': 'vendor_001', 'role': 'Vendor', 'ceo_id': 'ceo_123', ...}

# Rate limiting
from fastapi import Request

@router.post("/login")
async def login(request: Request):
    rate_limit(request, key="login", limit=5, period_seconds=60)
    # Raises HTTPException(429) if limit exceeded
```

**Rate Limiting**:
- In-memory storage (auto-cleanup after period)
- Per-IP tracking
- Configurable limits per endpoint

---

### 4. `logger.py` - Structured Logging
**Purpose**: JSON-structured logging with PII masking for CloudWatch compatibility.

**Key Features**:
- JSON output format (`pythonjsonlogger`)
- Automatic PII masking
- Contextual metadata (request_id, user_id, etc.)
- CloudWatch Logs integration

**Usage**:
```python
from common.logger import logger

# Basic logging
logger.info("User authenticated", extra={
    'user_id': 'vendor_001',
    'phone': '***4567',  # Masked
    'action': 'LOGIN'
})

# Error logging with context
logger.error("Database query failed", extra={
    'table': 'TrustGuard-Orders',
    'error': str(e),
    'order_id': 'order_123'
})
```

**Log Format**:
```json
{
  "timestamp": "2025-11-19T02:30:45.123Z",
  "level": "INFO",
  "message": "User authenticated",
  "user_id": "vendor_001",
  "phone": "***4567",
  "action": "LOGIN",
  "request_id": "a1b2c3d4"
}
```

---

### 5. `escalation_db.py` - Escalation Database Operations
**Purpose**: CRUD operations for high-value transaction escalations requiring CEO approval.

**Key Features**:
- Escalation creation with 24h TTL
- CEO dashboard queries (ByCEOPending GSI)
- Race condition protection (conditional updates)
- Automatic expiration handling

**Usage**:
```python
from common.escalation_db import (
    create_escalation,
    get_pending_escalations,
    update_escalation_status,
    get_escalation_summary
)

# Create escalation
escalation_id = create_escalation(
    order_id="order_123",
    ceo_id="ceo_001",
    vendor_id="vendor_456",
    buyer_id="wa_1234567890",
    amount=2500000.00,  # ₦2,500,000
    reason="HIGH_VALUE",
    notes="Large transaction requires review"
)

# Get CEO's pending escalations
pending = get_pending_escalations(ceo_id="ceo_001", limit=50)

# CEO approves escalation
update_escalation_status(
    escalation_id=escalation_id,
    status="APPROVED",
    approved_by="ceo_001",
    decision_notes="Verified with buyer via phone"
)

# Dashboard summary
summary = get_escalation_summary(ceo_id="ceo_001")
# Returns: {'total': 10, 'pending': 3, 'approved': 5, 'rejected': 2, ...}
```

**Escalation Lifecycle**:
```
1. Created (status=PENDING, expires_at=now+24h)
2. CEO Reviews (via dashboard)
3. CEO Decides (status=APPROVED/REJECTED, OTP required)
4. Auto-Expire (if no action within 24h, status=EXPIRED)
```

---

### 6. `sns_client.py` - Notification Helpers
**Purpose**: SNS-based notifications for CEO alerts and buyer updates.

**Key Features**:
- CEO escalation alerts (SMS + Email via SNS topic)
- Buyer order status notifications (SMS)
- Nigerian phone number formatting (E.164)
- PII masking in logs

**Usage**:
```python
from common.sns_client import (
    send_escalation_alert,
    send_buyer_notification,
    send_escalation_resolved_notification
)

# CEO alert for high-value transaction
send_escalation_alert(
    ceo_id="ceo_001",
    escalation_id="esc_a1b2c3",
    order_id="order_123",
    amount=2500000.00,
    reason="HIGH_VALUE",
    vendor_name="John's Electronics",
    buyer_masked_phone="4567"
)

# Buyer notification
send_buyer_notification(
    buyer_phone="+2348012345678",
    order_id="order_123",
    status="Under Review",
    additional_message="Your order will be reviewed within 24 hours."
)

# Post-decision notification
send_escalation_resolved_notification(
    ceo_id="ceo_001",
    escalation_id="esc_a1b2c3",
    order_id="order_123",
    decision="APPROVED",
    amount=2500000.00
)
```

**Phone Number Formatting**:
```python
# Accepts multiple Nigerian formats:
"08012345678"     → "+2348012345678"
"2348012345678"   → "+2348012345678"
"+2348012345678"  → "+2348012345678" (no change)
```

---

## 🔗 Dependencies

```txt
boto3>=1.40.0          # AWS SDK
pydantic>=2.0.0        # Settings validation
python-dotenv>=1.0.0   # .env file support
PyJWT>=2.8.0           # JWT handling
python-json-logger>=2.0.0  # Structured logging
```

---

## 🧪 Testing

```bash
# Test config loading
python -c "from common.config import settings; print(settings.USERS_TABLE)"

# Test database connection
python -c "from common.db_connection import dynamodb; print(dynamodb.meta.client)"

# Test JWT creation
python -c "from common.security import create_jwt; print(create_jwt('test', 'Vendor', 'ceo_1'))"

# Test logger
python -c "from common.logger import logger; logger.info('Test log')"
```

---

## 📋 Best Practices

### 1. **Never hardcode secrets**
```python
# ❌ BAD
JWT_SECRET = "hardcoded-secret-key"

# ✅ GOOD
from common.config import settings
jwt_secret = settings.get_jwt_secret()  # Fetches from Secrets Manager
```

### 2. **Always mask PII in logs**
```python
# ❌ BAD
logger.info(f"User logged in: {phone_number}")

# ✅ GOOD
masked_phone = phone_number[-4:] if len(phone_number) >= 4 else "****"
logger.info(f"User logged in: ***{masked_phone}")
```

### 3. **Use structured logging**
```python
# ❌ BAD
logger.info(f"Order {order_id} created by {user_id}")

# ✅ GOOD
logger.info("Order created", extra={
    'order_id': order_id,
    'user_id': user_id,
    'action': 'ORDER_CREATED'
})
```

### 4. **Validate inputs**
```python
from common.security import rate_limit

@router.post("/api/endpoint")
async def endpoint(request: Request):
    # Rate limit before processing
    rate_limit(request, key="endpoint", limit=10, period_seconds=60)
    
    # Validate JWT
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = decode_jwt(token)  # Raises exception if invalid
    
    # Process request...
```

---

## 🔐 Security Notes

- **JWT tokens**: HS256 algorithm, role-based expiry (Buyer: 10min, Vendor/CEO: 30min)
- **Secrets rotation**: Secrets Manager supports automatic rotation (configure in AWS Console)
- **Rate limiting**: In-memory only (use Redis/ElastiCache for production multi-Lambda)
- **PII handling**: Always mask phone numbers (show last 4 digits), encrypt email addresses in logs

---

## 🚀 Future Enhancements

- [ ] Redis-backed rate limiting for multi-Lambda deployments
- [ ] Distributed tracing with AWS X-Ray
- [ ] Metrics collection with CloudWatch custom metrics
- [ ] Secret caching with TTL for performance (trade-off with Zero Trust)
- [ ] Input validation decorators for common patterns

---

**Last Updated**: 19 November 2025  
**Maintainer**: Senior Cloud Architect
