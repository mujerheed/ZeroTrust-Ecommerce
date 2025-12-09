# Webhook Testing Summary

**Date:** December 8, 2025  
**Status:** ✅ Webhooks Receiving Successfully (with minor fix needed)

---

## ✅ What's Working

### 1. **Webhook Delivery** ✅
- WhatsApp webhooks reaching AWS Lambda
- Instagram webhooks reaching AWS Lambda
- HMAC signature verification working correctly

### 2. **Message Parsing** ✅
- WhatsApp messages parsed successfully
  - Example: Sender `16315551181`, Text: "this is a text message"
- Instagram messages parsed successfully
  - Example: Sender PSID `2494432963985342`

### 3. **Security** ✅
- X-Hub-Signature-256 validation working
- Meta App Secret verification successful
- Secrets Manager integration working

---

## ⚠️ Issue Found & Fixed

### **Problem:**
```
ImportError: cannot import name 'get_dynamodb_table' from 'common.db_connection'
```

### **Root Cause:**
`conversation_state.py` was importing a function that didn't exist in `db_connection.py`

### **Fix Applied:**
Added `get_dynamodb_table()` helper function to `common/db_connection.py`

```python
def get_dynamodb_table(table_name: str):
    """Get a DynamoDB table resource by name."""
    return dynamodb.Table(table_name)
```

### **Next Step:**
Redeploy to AWS Lambda to apply the fix:

```bash
cd infrastructure/cloudformation
sam build
sam deploy
```

---

## 📊 Log Analysis

### WhatsApp Webhook Log (05:39:40 UTC):
```json
{
  "message": "WhatsApp webhook received",
  "object": "whatsapp_business_account",
  "sender": "16315551181",
  "type": "text",
  "text_preview": "this is a text message",
  "ceo_id": "ceo_dev_default"
}
```

### Instagram Webhook Log (05:44:37 UTC):
```json
{
  "message": "Instagram webhook received",
  "object": "instagram",
  "sender_psid": "2494432963985342",
  "ceo_id": "ceo_dev_default"
}
```

---

## 🔄 Deployment Instructions

### 1. Build Lambda Package
```bash
cd infrastructure/cloudformation
sam build
```

### 2. Deploy to AWS
```bash
sam deploy
```

### 3. Test Again
Send test message from Meta App Dashboard or real WhatsApp/Instagram message

### 4. Verify Logs
```bash
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1
```

Expected output (after fix):
```
✅ Webhook signature verified successfully
✅ WhatsApp webhook received
✅ WhatsApp message parsed
✅ Processing message
✅ Message routed to chatbot
✅ Response sent
```

---

## 📝 Notes

1. **CEO ID Mapping:**
   - Currently using default CEO ID: `ceo_dev_default`
   - To map to specific CEOs, need to store phone_number_id → ceo_id mapping in DynamoDB

2. **Instagram Access Token Warning:**
   ```
   "Instagram access token not configured"
   ```
   - This is expected if you haven't connected Instagram via OAuth yet
   - Connect via CEO Dashboard → Integrations → Connect Instagram

3. **WhatsApp Test Number:**
   - Sender `16315551181` is Meta's test number
   - Real production numbers will have different format

---

## ✅ Success Criteria Met

- [x] Webhooks reaching AWS Lambda
- [x] HMAC signature validation working
- [x] Message parsing successful
- [x] Sender identification working
- [ ] Chatbot processing (blocked by ImportError - **FIXED, needs redeploy**)
- [ ] Response sending (pending chatbot fix)

---

**Status:** Ready for redeployment to complete webhook integration! 🚀
