# Why You're Not Receiving Replies - Quick Fix Guide

## 🎯 The Issue

✅ **Webhooks are working** - Your backend is receiving messages  
✅ **Message parsing is working** - Messages are being processed  
✅ **Chatbot logic is working** - Responses are being generated  
❌ **Sending replies is failing** - No WhatsApp/Instagram access tokens configured

---

## 🔍 What's Happening

When you send a message:
1. ✅ Meta sends webhook to your AWS Lambda
2. ✅ Lambda receives and parses the message
3. ✅ Chatbot generates a response
4. ❌ **Chatbot tries to send reply but fails** (no access token)
5. ❌ You don't receive the reply

**From CloudWatch logs:**
```
"Instagram access token not configured"
```

---

## ✅ Solution: Configure Access Tokens

You need to store your WhatsApp/Instagram access tokens in AWS Secrets Manager.

### **Step 1: Get Your Access Tokens**

#### For WhatsApp:
1. Go to [Meta App Dashboard](https://developers.facebook.com/apps/850791007281950/)
2. Click **WhatsApp** → **API Setup**
3. Find **"Temporary access token"** or **"System User Token"**
4. Copy the token (starts with `EAA...`)

#### For Instagram:
1. Complete OAuth flow via CEO Dashboard → Integrations → Connect Instagram
2. OR get token from Meta App Dashboard → Instagram → Basic Display
3. Copy the access token

---

### **Step 2: Store Tokens in AWS Secrets Manager**

```bash
# Update Meta secrets with your tokens
aws secretsmanager update-secret \
  --secret-id /TrustGuard/dev/meta-TrustGuard-Dev \
  --region us-east-1 \
  --secret-string '{
    "APP_ID": "850791007281950",
    "APP_SECRET": "5ba4cd58e7205ecd439cf49ac11c7adb",
    "WEBHOOK_VERIFY_TOKEN": "test_trustgu@rd_25",
    "WHATSAPP_ACCESS_TOKEN": "YOUR_WHATSAPP_TOKEN_HERE",
    "WHATSAPP_PHONE_NUMBER_ID": "YOUR_PHONE_NUMBER_ID_HERE",
    "INSTAGRAM_ACCESS_TOKEN": "YOUR_INSTAGRAM_TOKEN_HERE",
    "INSTAGRAM_PAGE_ID": "YOUR_PAGE_ID_HERE"
  }'
```

**Replace:**
- `YOUR_WHATSAPP_TOKEN_HERE` - Your WhatsApp access token from Meta
- `YOUR_PHONE_NUMBER_ID_HERE` - WhatsApp Phone Number ID (from API Setup page)
- `YOUR_INSTAGRAM_TOKEN_HERE` - Your Instagram access token
- `YOUR_PAGE_ID_HERE` - Your Instagram Page ID

---

### **Step 3: Verify Secrets**

```bash
# Check secrets are stored correctly
aws secretsmanager get-secret-value \
  --secret-id /TrustGuard/dev/meta-TrustGuard-Dev \
  --region us-east-1 \
  --query SecretString \
  --output text | python3 -m json.tool
```

---

### **Step 4: Test Again**

1. Send a WhatsApp message to Meta's test number
2. Check CloudWatch logs:
   ```bash
   aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1
   ```
3. You should see:
   ```
   "WhatsApp message sent" ✅
   ```
4. **You'll receive a reply on your phone!** 📱

---

## 🚀 Alternative: Use OAuth (Recommended)

Instead of manually copying tokens, use the OAuth flow:

### **For WhatsApp:**
1. Go to CEO Dashboard: `http://localhost:3000/ceo/integrations`
2. Click **"Connect WhatsApp Business"**
3. Complete OAuth flow
4. Token automatically stored in Secrets Manager ✅

### **For Instagram:**
1. Go to CEO Dashboard: `http://localhost:3000/ceo/integrations`
2. Click **"Connect Instagram"**
3. Complete OAuth flow
4. Token automatically stored in Secrets Manager ✅

---

## 📋 Quick Checklist

- [ ] Get WhatsApp access token from Meta App Dashboard
- [ ] Get WhatsApp Phone Number ID
- [ ] Get Instagram access token (or use OAuth)
- [ ] Update AWS Secrets Manager with tokens
- [ ] Verify secrets are stored correctly
- [ ] Test by sending a message
- [ ] Check CloudWatch logs for "message sent"
- [ ] Receive reply on your phone! 🎉

---

## 🔍 How to Find Phone Number ID

1. Go to [Meta App Dashboard](https://developers.facebook.com/apps/850791007281950/)
2. Click **WhatsApp** → **API Setup**
3. Look for **"Phone Number ID"** (looks like: `123456789012345`)
4. Copy this number

---

## ⚠️ Token Expiry

**Temporary tokens expire in 24 hours!**

For production, you need **permanent tokens**:
1. Create a **System User** in Meta Business Manager
2. Generate a **permanent token** for that user
3. OR use OAuth (tokens auto-refresh)

---

## 🎯 Summary

**Why no replies:**
- Webhooks work ✅
- Chatbot logic works ✅
- **Missing:** WhatsApp/Instagram access tokens ❌

**Fix:**
1. Get tokens from Meta App Dashboard
2. Store in AWS Secrets Manager
3. Test again
4. Receive replies! 🎉

**Easiest way:**
Use OAuth via CEO Dashboard → Integrations (auto-configures everything!)

---

**Last Updated:** December 8, 2025
