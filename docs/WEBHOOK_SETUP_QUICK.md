# Quick Webhook Setup Guide

## Problem: Meta Test Shows "Success" But No Logs in Terminal

### Root Cause
Meta is sending webhooks to the wrong URL. Your backend expects:
- ✅ `/integrations/webhook/whatsapp`
- ✅ `/integrations/webhook/instagram`

But Meta might be configured to send to:
- ❌ `/webhook` (404 Not Found)

---

## Solution: Update Meta Webhook URL

### Step 1: Find Your Webhook URL

**If using ngrok:**
```bash
# Terminal: Start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
# Your webhook URLs are:
# WhatsApp: https://abc123.ngrok-free.app/integrations/webhook/whatsapp
# Instagram: https://abc123.ngrok-free.app/integrations/webhook/instagram
```

**If deployed to AWS:**
```bash
# Your API Gateway URL (e.g., https://xyz.execute-api.us-east-1.amazonaws.com)
# Webhook URLs:
# WhatsApp: https://xyz.execute-api.us-east-1.amazonaws.com/integrations/webhook/whatsapp
# Instagram: https://xyz.execute-api.us-east-1.amazonaws.com/integrations/webhook/instagram
```

---

### Step 2: Configure Meta App Webhooks

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Select your app
3. Click **Webhooks** in left sidebar

#### For WhatsApp:
1. Find **WhatsApp** section
2. Click **Edit** next to Callback URL
3. Enter: `https://YOUR_URL/integrations/webhook/whatsapp`
4. Verify Token: `trustguard_verify_2025` (or your configured token from `.env`)
5. Click **Verify and Save**
6. Subscribe to fields:
   - ✅ `messages`
   - ✅ `messaging_postbacks` (optional)

#### For Instagram:
1. Find **Instagram** section
2. Click **Edit** next to Callback URL
3. Enter: `https://YOUR_URL/integrations/webhook/instagram`
4. Verify Token: `trustguard_verify_2025`
5. Click **Verify and Save**
6. Subscribe to fields:
   - ✅ `messages`
   - ✅ `messaging_postbacks` (optional)

---

### Step 3: Test the Webhook

#### Method 1: Meta Test Button
1. In Meta App Dashboard → Webhooks
2. Click **Test** button next to your webhook
3. Select `messages` event
4. Click **Send to My Server**
5. **Check your terminal** - you should see:
   ```
   ================================================================================
   🔔 WHATSAPP WEBHOOK RECEIVED!
   ================================================================================
   ```

#### Method 2: Manual cURL Test
```bash
# Test WhatsApp webhook locally
curl -X POST http://localhost:8000/integrations/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "1234567890",
            "text": {"body": "Test message"}
          }]
        }
      }]
    }]
  }'

# You should see in terminal:
# ================================================================================
# 🔔 WHATSAPP WEBHOOK RECEIVED!
# ================================================================================
```

#### Method 3: Real WhatsApp Message
1. Join WhatsApp sandbox (send `join YOUR-CODE` to sandbox number)
2. Send a message: `Hello TrustGuard`
3. Check terminal for webhook notification

---

## Troubleshooting

### Issue: Still No Logs After Meta Test

**Check 1: Correct URL?**
```bash
# Your webhook URL MUST include /integrations/webhook/whatsapp
# NOT just /webhook

# Correct:
https://abc123.ngrok-free.app/integrations/webhook/whatsapp

# Wrong:
https://abc123.ngrok-free.app/webhook  ❌
```

**Check 2: Backend Running?**
```bash
# Terminal should show:
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Check 3: ngrok Active?**
```bash
# ngrok terminal should show:
Session Status                online
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Check 4: Test Endpoint Directly**
```bash
# Should return 404 (wrong URL):
curl http://localhost:8000/webhook

# Should return 200 (correct URL):
curl -X POST http://localhost:8000/integrations/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"object":"whatsapp_business_account"}'
```

---

## Expected Terminal Output

When webhook is working correctly, you'll see:

```
================================================================================
🔔 WHATSAPP WEBHOOK RECEIVED!
================================================================================

INFO:     127.0.0.1:54321 - "POST /integrations/webhook/whatsapp HTTP/1.1" 200 OK
```

Or for Instagram:

```
================================================================================
📸 INSTAGRAM WEBHOOK RECEIVED!
================================================================================

INFO:     127.0.0.1:54321 - "POST /integrations/webhook/instagram HTTP/1.1" 200 OK
```

---

## Quick Reference

| Platform | Webhook URL | Verify Token |
|----------|-------------|--------------|
| WhatsApp | `https://YOUR_URL/integrations/webhook/whatsapp` | `trustguard_verify_2025` |
| Instagram | `https://YOUR_URL/integrations/webhook/instagram` | `trustguard_verify_2025` |

**Environment Variable:**
```bash
# In backend/.env
META_WEBHOOK_VERIFY_TOKEN=trustguard_verify_2025
```

---

**Last Updated**: December 8, 2025
