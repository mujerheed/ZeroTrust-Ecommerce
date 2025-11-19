# Password Authentication Removal - Zero Trust Implementation

**Date:** November 20, 2025  
**Status:** ✅ DEPLOYED & OPERATIONAL  
**Deployment:** TrustGuard-Dev (us-east-1)

---

## Summary

Successfully removed all password-based authentication from the CEO and Vendor services, migrating to 100% OTP-based authentication in compliance with Zero Trust security principles.

---

## Changes Implemented

### 1. CEO Registration (backend/ceo_service/ceo_routes.py)

**BEFORE:**
```python
class CEORegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str  # ❌ Password required
    company_name: Optional[str] = None
```

**AFTER:**
```python
class CEORegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company_name: Optional[str] = None  # ✅ No password
```

**New Flow:**
1. POST `/ceo/register` with `{ name, email, phone, company_name }`
2. System generates 6-character OTP (digits + symbols: `0-9!@#$%^&*`)
3. OTP sent via SMS to phone + Email
4. CEO verifies with POST `/auth/verify-otp`
5. Returns JWT token

---

### 2. CEO Login (backend/ceo_service/ceo_routes.py)

**BEFORE:**
```python
class CEOLoginRequest(BaseModel):
    email: EmailStr
    password: str  # ❌ Password authentication
```

**AFTER:**
```python
class CEOLoginRequest(BaseModel):
    contact: str  # ✅ Phone or email for OTP delivery
```

**New Flow:**
1. POST `/ceo/login` with `{ contact: "email or phone" }`
2. System generates 6-character OTP
3. OTP sent via SMS/Email
4. CEO verifies with POST `/auth/verify-otp`
5. Returns JWT token

---

### 3. Vendor Onboarding (backend/ceo_service/ceo_routes.py)

**BEFORE:**
```python
class VendorOnboardRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: Optional[str] = None  # ❌ Optional password
```

**AFTER:**
```python
class VendorOnboardRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str  # ✅ No password field
```

**New Flow:**
1. CEO creates vendor via POST `/ceo/vendors`
2. System generates 8-character OTP (alphanumeric + special chars)
3. OTP sent to vendor via SMS
4. Vendor logs in with POST `/auth/vendor/login { phone }`
5. Vendor verifies with POST `/auth/verify-otp`
6. Returns JWT token for vendor dashboard

---

### 4. Password Functions Removed (backend/ceo_service/ceo_logic.py)

**DELETED:**
- `hash_password(password: str) -> str` ❌
- `verify_password(password: str, password_hash: str) -> bool` ❌
- `authenticate_ceo(email: str, password: str) -> Dict[str, Any]` ❌

**REPLACED WITH:**
```python
def register_ceo(name: str, email: str, phone: str, company_name: str = None) -> Dict[str, Any]:
    """
    Register CEO with OTP verification (Zero Trust).
    """
    # Create CEO record (no password)
    ceo_record = create_ceo(name, email, phone, company_name)
    
    # Generate and send OTP
    otp = generate_ceo_otp()  # 6-char: 0-9!@#$%^&*
    store_ceo_otp(ceo_record["ceo_id"], otp)
    
    # Send via SMS + Email
    send_otp_via_sms(phone, otp)
    send_otp_via_email(email, otp)
    
    return ceo_record
```

---

### 5. Database Schema Updated (backend/ceo_service/database.py)

**BEFORE:**
```python
def create_ceo(name: str, email: str, phone: str, password_hash: str, company_name: str = None):
    ceo_record = {
        "user_id": ceo_id,
        "password_hash": password_hash,  # ❌ Stored password hash
        "verified": True,
        # ... other fields
    }
```

**AFTER:**
```python
def create_ceo(name: str, email: str, phone: str, company_name: str = None):
    ceo_record = {
        "user_id": ceo_id,
        # NO password_hash field ✅
        "verified": False,  # ✅ Verified via OTP
        # ... other fields
    }
```

**DynamoDB Users Table Changes:**
- ❌ Removed: `password_hash` field for CEOs
- ✅ Changed: `verified` defaults to `False` (verified via OTP)

---

## OTP Format Standards

### CEO OTP
- **Format:** 6 characters (digits + symbols: `0-9!@#$%^&*`)
- **Example:** `7!3@9%`
- **TTL:** 5 minutes (300 seconds)
- **Single-use:** Deleted after successful verification
- **Delivery:** SMS (primary) + Email (fallback)

### Vendor OTP
- **Format:** 8 characters (alphanumeric + special chars: `A-Za-z0-9!@#$%^&*`)
- **Example:** `aB9!x3@Z`
- **TTL:** 5 minutes (300 seconds)
- **Single-use:** Deleted after successful verification
- **Delivery:** SMS to phone number

### Buyer OTP
- **Format:** 8 characters (alphanumeric + special chars)
- **TTL:** 5 minutes
- **Single-use:** Deleted after verification
- **Delivery:** WhatsApp/Instagram DM (primary), SMS (fallback)

---

## Authentication Flows

### CEO Registration Flow

```
┌──────────┐                                    ┌──────────────┐
│  CEO     │                                    │  Backend     │
│  (Web)   │                                    │  API         │
└────┬─────┘                                    └──────┬───────┘
     │                                                 │
     │  POST /ceo/register                             │
     │  { name, email, phone, company_name }           │
     ├────────────────────────────────────────────────>│
     │                                                 │
     │                                                 │  Create CEO record
     │                                                 │  (verified: false)
     │                                                 │
     │                                                 │  Generate 6-char OTP
     │                                                 │  (digits + symbols)
     │                                                 │
     │                                                 │  Store in DynamoDB
     │                                                 │  (TTL: 5 min)
     │                                                 │
     │                                                 │  Send SMS → Phone
     │                                                 │  Send Email → Email
     │                                                 │
     │  200 OK                                         │
     │  { ceo_id, message: "Check SMS/Email for OTP" } │
     │<────────────────────────────────────────────────┤
     │                                                 │
     │                                                 │
     │  POST /auth/verify-otp                          │
     │  { ceo_id, otp, role: "CEO" }                   │
     ├────────────────────────────────────────────────>│
     │                                                 │
     │                                                 │  Verify OTP
     │                                                 │  Delete OTP
     │                                                 │  Mark verified: true
     │                                                 │  Generate JWT
     │                                                 │
     │  200 OK                                         │
     │  { token, role: "CEO", ceo_id }                 │
     │<────────────────────────────────────────────────┤
     │                                                 │
     │  Use JWT for all subsequent requests            │
     │                                                 │
```

### CEO Login Flow

```
┌──────────┐                                    ┌──────────────┐
│  CEO     │                                    │  Backend     │
│  (Web)   │                                    │  API         │
└────┬─────┘                                    └──────┬───────┘
     │                                                 │
     │  POST /ceo/login                                │
     │  { contact: "email or phone" }                  │
     ├────────────────────────────────────────────────>│
     │                                                 │
     │                                                 │  Find CEO by email/phone
     │                                                 │
     │                                                 │  Generate 6-char OTP
     │                                                 │
     │                                                 │  Store in DynamoDB
     │                                                 │  (TTL: 5 min)
     │                                                 │
     │                                                 │  Send SMS/Email
     │                                                 │
     │  200 OK                                         │
     │  { message: "OTP sent via SMS/Email" }          │
     │<────────────────────────────────────────────────┤
     │                                                 │
     │                                                 │
     │  POST /auth/verify-otp                          │
     │  { ceo_id, otp, role: "CEO" }                   │
     ├────────────────────────────────────────────────>│
     │                                                 │
     │                                                 │  Verify OTP
     │                                                 │  Delete OTP
     │                                                 │  Generate JWT
     │                                                 │
     │  200 OK                                         │
     │  { token, role: "CEO", ceo_id }                 │
     │<────────────────────────────────────────────────┤
     │                                                 │
```

---

## Security Benefits

### 1. No Password Storage
- **Before:** Bcrypt hashed passwords in DynamoDB
- **After:** No `password_hash` field, cannot be stolen or leaked
- **Impact:** Eliminates password breach risk

### 2. Time-Limited Credentials
- **Before:** Passwords valid indefinitely until changed
- **After:** OTPs expire in 5 minutes
- **Impact:** Reduces attack window to 300 seconds

### 3. Single-Use Tokens
- **Before:** Passwords reusable until changed
- **After:** OTPs deleted after verification
- **Impact:** Prevents replay attacks

### 4. Multi-Channel Delivery
- **Before:** Single email/password login
- **After:** SMS (primary) + Email (fallback)
- **Impact:** Verifies user has access to registered phone/email

### 5. Audit Trail
- **Before:** Login attempts logged
- **After:** OTP generation, delivery, and verification all logged
- **Impact:** Complete authentication event trail for forensics

### 6. Zero Trust Compliance
- **Principle:** "Never trust, always verify"
- **Implementation:** Every login requires fresh OTP verification
- **Impact:** Aligns with NIST 800-207 Zero Trust Architecture

---

## Deployment Status

**Stack:** TrustGuard-Dev  
**Region:** us-east-1  
**Status:** ✅ UPDATE_COMPLETE  
**Deployment Time:** November 20, 2025, 01:52 UTC

### Updated Lambda Functions
- ✅ `AuthService` - OTP generation and verification
- ✅ `CEOService` - CEO registration and login (OTP-based)
- ✅ `VendorService` - Vendor onboarding (OTP-based)
- ✅ `ReceiptService` - Receipt handling

### API Endpoint
```
https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/
```

### Test CEO Registration
```bash
curl -X POST https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/ceo/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+2348012345678",
    "company_name": "ABC Trading"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "CEO registration initiated. Check SMS/Email for 6-digit OTP to complete setup.",
  "data": {
    "ceo": {
      "ceo_id": "ceo_abc123xyz",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+2348012345678",
      "verified": false
    },
    "otp_format": "6-digit numbers + symbols",
    "ttl_minutes": 5
  }
}
```

### Test OTP Verification
```bash
curl -X POST https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "ceo_id": "ceo_abc123xyz",
    "otp": "7!3@9%",
    "role": "CEO"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "OTP verified successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "role": "CEO",
    "ceo_id": "ceo_abc123xyz"
  }
}
```

---

## Migration Notes

### Existing CEO Accounts
⚠️ **IMPORTANT:** Existing CEO accounts with `password_hash` field:
1. Will not be automatically migrated
2. Should use "Forgot Password" → OTP reset flow
3. Or contact admin for manual migration

### Backward Compatibility
❌ **NOT MAINTAINED:**
- Old password-based login endpoints removed
- Clients must update to OTP-based flow
- Frontend must implement OTP verification UI

### Database Cleanup
To remove `password_hash` from existing CEO records:
```python
# Run this migration script (ONCE ONLY):
from backend.common.db_connection import get_dynamodb_table

USERS_TABLE = get_dynamodb_table("TrustGuard-Users")

def cleanup_password_hashes():
    response = USERS_TABLE.scan(
        FilterExpression="attribute_exists(password_hash) AND #role = :role",
        ExpressionAttributeNames={"#role": "role"},
        ExpressionAttributeValues={":role": "CEO"}
    )
    
    for item in response.get("Items", []):
        USERS_TABLE.update_item(
            Key={"user_id": item["user_id"]},
            UpdateExpression="REMOVE password_hash SET verified = :false",
            ExpressionAttributeValues={":false": False}
        )
        print(f"Cleaned password_hash from CEO: {item['user_id']}")

if __name__ == "__main__":
    cleanup_password_hashes()
```

---

## Next Steps (Remaining Requirements)

### Priority 1: Conversational State Management
**Goal:** Multi-turn buyer registration with name/address collection

**Implementation:**
1. Create DynamoDB `ConversationState` table
2. Add state machine to `chatbot_router.py`:
   - `waiting_for_name` → `waiting_for_address` → `waiting_for_phone` (IG only) → `verified`
3. Store conversation context between messages
4. Handle interruptions (e.g., user types "cancel" mid-flow)

**Example Flow:**
```
Buyer: "hello"
Bot: "Welcome! What's your name?"
→ State: waiting_for_name

Buyer: "Sarah Johnson"
Bot: "Nice to meet you, Sarah! What's your delivery address?"
→ State: waiting_for_address

Buyer: "123 Ikeja Road, Lagos"
Bot: "Perfect! I'll send an OTP to verify your WhatsApp number."
→ Generate OTP, state: waiting_for_otp
```

---

### Priority 2: Auto Media Download
**Goal:** Automatically download receipt images from Meta and upload to S3

**Implementation:**
```python
async def handle_receipt_media(media_id: str, platform: str, ceo_id: str, order_id: str):
    """
    Download receipt image from Meta and upload to S3.
    """
    # Get media URL from Meta Graph API
    if platform == "whatsapp":
        media_url = await whatsapp_api.get_media_url(media_id)
    else:
        media_url = await instagram_api.get_media_url(media_id)
    
    # Download media content
    media_content = await download_media(media_url, access_token)
    
    # Upload to S3
    s3_key = f"receipts/{ceo_id}/{order_id}/{media_id}.jpg"
    upload_to_s3(media_content, s3_key)
    
    # Store metadata in DynamoDB
    store_receipt_metadata(order_id, s3_key, media_id)
```

**Meta Graph API Endpoints:**
- WhatsApp: `GET https://graph.facebook.com/v18.0/{media_id}` (requires `WHATSAPP_ACCESS_TOKEN`)
- Instagram: `GET https://graph.facebook.com/v18.0/{media_id}` (requires `PAGE_ACCESS_TOKEN`)

---

### Priority 3: Address Confirmation
**Goal:** Confirm delivery address before order finalization

**Implementation:**
```python
async def handle_order_confirmation(buyer_id: str, order_id: str, address: str):
    """
    Send address confirmation prompt before finalizing order.
    """
    message = f"""
    📦 Order Ready for Confirmation
    
    Delivery Address:
    {address}
    
    Reply with:
    - "confirm" to proceed
    - "update address to [new address]" to change
    """
    
    await send_message(buyer_id, message)
    
    # Set conversation state
    set_conversation_state(buyer_id, "waiting_for_address_confirmation", {
        "order_id": order_id,
        "current_address": address
    })
```

---

### Priority 4: Transaction PDF Summary
**Goal:** Generate PDF invoice after order completion

**Implementation:**
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def generate_order_pdf(order: dict) -> bytes:
    """
    Generate PDF summary of completed order.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 750, "TrustGuard Order Summary")
    
    # Order details
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 700, f"Order ID: {order['order_id']}")
    pdf.drawString(100, 680, f"Date: {order['created_at']}")
    pdf.drawString(100, 660, f"Buyer: {order['buyer_name']}")
    pdf.drawString(100, 640, f"Vendor: {order['vendor_name']}")
    
    # Items
    y = 600
    for item in order['items']:
        pdf.drawString(100, y, f"{item['name']} - ₦{item['price']:,.2f}")
        y -= 20
    
    # Total
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, y - 20, f"Total: ₦{order['total_amount']:,.2f}")
    
    pdf.save()
    return buffer.getvalue()

async def send_order_receipt(buyer_id: str, order_id: str):
    """
    Generate and send order PDF to buyer.
    """
    order = get_order_by_id(order_id)
    pdf_content = generate_order_pdf(order)
    
    # Upload to S3
    s3_key = f"receipts/{order['ceo_id']}/{order_id}/invoice.pdf"
    upload_to_s3(pdf_content, s3_key)
    
    # Generate presigned URL (valid 7 days)
    download_url = generate_presigned_url(s3_key, expires_in=604800)
    
    # Send to buyer
    message = f"""
    ✅ Order Completed!
    
    Your order #{order_id} has been delivered.
    
    Download invoice: {download_url}
    
    Thank you for using TrustGuard! 🎉
    """
    await send_message(buyer_id, message)
```

---

## Completion Status

### Authentication & Security (100% Complete)
- ✅ CEO OTP-based registration
- ✅ CEO OTP-based login
- ✅ Vendor OTP-based onboarding
- ✅ Buyer OTP-based verification (WhatsApp/Instagram)
- ✅ Password functions removed
- ✅ Database schema updated
- ✅ Multi-channel OTP delivery (SMS + Email)
- ✅ Audit logging

### Meta Integration (100% Complete)
- ✅ WhatsApp Business API integration
- ✅ Instagram Messaging API integration
- ✅ OAuth 2.0 connection flow
- ✅ HMAC webhook verification
- ✅ Multi-CEO tenancy routing

### Remaining Features (4 items)
- ⏳ Conversational state management (Priority 1)
- ⏳ Auto media download (Priority 2)
- ⏳ Address confirmation flow (Priority 3)
- ⏳ Transaction PDF summary (Priority 4)

**Estimated Time to 100%:** 1-2 days of focused development

---

## References

- [NIST 800-207: Zero Trust Architecture](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf)
- [Meta WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Meta Instagram Messaging API Documentation](https://developers.facebook.com/docs/messenger-platform)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)

---

**Document Version:** 1.0  
**Last Updated:** November 20, 2025  
**Author:** TrustGuard Development Team
