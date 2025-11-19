# Meta Integration Setup Guide

This guide walks you through setting up WhatsApp Business API and Instagram Messaging API integration with TrustGuard.

## Prerequisites

- Meta Business Account
- Facebook Page (for Instagram)
- WhatsApp Business API access
- Instagram Business Account connected to Facebook Page

## Step 1: Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" as app type
4. Fill in app details:
   - **App Name**: TrustGuard
   - **App Contact Email**: your-email@domain.com
   - **Business Account**: Select your business
5. Click "Create App"

6. Note your **App ID** and **App Secret**:
   - App ID: Found in app dashboard
   - App Secret: Settings → Basic → Show App Secret

**✅ You already have these credentials seeded:**
- APP_ID: `850791007281950`
- APP_SECRET: `5ba4cd58e7205ecd439cf49ac11c7adb`

---

## Step 2: WhatsApp Business API Setup

### 2.1 Add WhatsApp Product

1. In your Meta App, go to "Add Product"
2. Select "WhatsApp" → "Set Up"
3. Choose your Business Account
4. Click "Continue"

### 2.2 Get Phone Number ID

1. Go to WhatsApp → "API Setup"
2. You'll see a **Test Number** (temporary for development)
   - Or add your own Business Phone Number
3. Copy the **Phone Number ID** (format: `123456789012345`)

### 2.3 Generate Access Token

**For Testing (60 days):**
1. WhatsApp → API Setup
2. Click "Generate Token" next to your phone number
3. Copy the temporary access token

**For Production (Long-Lived):**
1. Go to Tools → Access Token Tool
2. Select your app and page
3. Generate long-lived token (never expires if used regularly)
4. Copy the access token

### 2.4 Configure Webhook

1. WhatsApp → Configuration
2. Click "Edit" next to "Webhook"
3. Enter webhook URL:
   ```
   https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp
   ```
4. Enter verify token: `trustguard_verify_2025`
5. Click "Verify and Save"

6. Subscribe to webhook fields:
   - ✅ `messages`

---

## Step 3: Instagram Messaging API Setup

### 3.1 Add Messenger Product

1. In your Meta App, go to "Add Product"
2. Select "Messenger" → "Set Up"

### 3.2 Connect Instagram Account

1. Messenger → Settings
2. Under "Instagram Integration", click "Connect Account"
3. Log in to your Instagram Business Account
4. Select the Facebook Page connected to your Instagram
5. Grant permissions

### 3.3 Get Page ID

1. Go to your Facebook Page
2. Settings → General
3. Copy **Page ID** (numeric)

Or use Graph API:
```bash
curl -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_USER_ACCESS_TOKEN"
```

### 3.4 Generate Page Access Token

**For Testing:**
1. Tools → Graph API Explorer
2. Select your app
3. Select your page from "User or Page" dropdown
4. Click "Generate Access Token"
5. Grant permissions: `pages_messaging`, `instagram_basic`, `instagram_manage_messages`

**For Production:**
1. Use OAuth flow from CEO dashboard (implemented in `ceo_service/oauth_meta.py`)
2. URL: `https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/ceo/oauth/meta/authorize`

### 3.5 Configure Webhook

1. Messenger → Settings → Webhooks
2. Click "Add Callback URL"
3. Enter webhook URL:
   ```
   https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/instagram
   ```
4. Enter verify token: `trustguard_verify_2025`
5. Click "Verify and Save"

6. Subscribe to webhook fields:
   - ✅ `messages`
   - ✅ `messaging_postbacks`

---

## Step 4: Update Secrets in AWS Secrets Manager

You've already seeded the Meta secret with APP_ID and APP_SECRET. Now you need to add the OAuth tokens for your CEO account.

### 4.1 Get Your CEO ID

After registering as CEO via the API:
```bash
curl -X POST "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/auth/ceo/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Name",
    "email": "your-email@example.com",
    "phone": "+2348012345678",
    "business_name": "Your Business"
  }'
```

Response will include your `ceo_id` (e.g., `ceo_1763578952293`).

### 4.2 Update Secret with OAuth Tokens

Use the AWS CLI or Console:

**Via AWS CLI:**
```bash
# Get current secret value
aws secretsmanager get-secret-value \
  --secret-id "/TrustGuard/dev/meta-TrustGuard-Dev" \
  --region us-east-1 \
  --query 'SecretString' --output text > meta_secret.json

# Edit meta_secret.json to add ceo_oauth_tokens
# Structure:
{
  "APP_ID": "850791007281950",
  "APP_SECRET": "5ba4cd58e7205ecd439cf49ac11c7adb",
  "ceo_oauth_tokens": {
    "ceo_1763578952293": {
      "access_token": "YOUR_WHATSAPP_ACCESS_TOKEN",
      "whatsapp_phone_id": "YOUR_PHONE_NUMBER_ID",
      "instagram_page_id": "YOUR_PAGE_ID",
      "expires_at": null
    }
  }
}

# Update secret
aws secretsmanager update-secret \
  --secret-id "/TrustGuard/dev/meta-TrustGuard-Dev" \
  --secret-string file://meta_secret.json \
  --region us-east-1
```

**Via AWS Console:**
1. Go to AWS Secrets Manager
2. Find secret: `/TrustGuard/dev/meta-TrustGuard-Dev`
3. Click "Retrieve secret value" → "Edit"
4. Update JSON to add `ceo_oauth_tokens` section
5. Save

---

## Step 5: Test Webhook Integration

### 5.1 Test Health Endpoint

```bash
curl https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "TrustGuard Meta Webhooks",
  "endpoints": {
    "whatsapp": "/integrations/webhook/whatsapp",
    "instagram": "/integrations/webhook/instagram"
  }
}
```

### 5.2 Test WhatsApp Message

1. Send a message to your WhatsApp Business Number
2. Type: `register`
3. Check CloudWatch Logs:
   ```bash
   aws logs tail /aws/lambda/TrustGuard-AuthService-dev --follow
   ```

Expected flow:
- Webhook receives message
- Signature verified
- Message parsed
- Buyer created in Users table
- OTP sent via WhatsApp DM

### 5.3 Test Instagram Message

1. Send a DM to your Instagram Business Account
2. Type: `hi`
3. Check CloudWatch Logs

---

## Step 6: Buyer Registration Flow

Once webhooks are working, test the full buyer flow:

1. **Buyer sends "register" via WhatsApp/Instagram**
   - System creates buyer record with `buyer_id` = `wa_<phone>` or `ig_<psid>`
   - Sends welcome message

2. **Buyer sends OTP**
   - System verifies 8-character OTP
   - Generates JWT token
   - Buyer is now authenticated

3. **Buyer can now:**
   - Confirm orders: `confirm ord_123`
   - Check status: `order ord_123`
   - Upload receipts

---

## Troubleshooting

### Webhook Not Receiving Messages

1. **Check webhook URL is accessible:**
   ```bash
   curl https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp
   ```
   Should return 405 Method Not Allowed (GET not supported, only POST)

2. **Verify Meta webhook subscription:**
   - Go to WhatsApp → Configuration → Webhook
   - Check green checkmark next to webhook URL
   - Re-verify if needed

3. **Check CloudWatch Logs for signature errors:**
   ```bash
   aws logs tail /aws/lambda/TrustGuard-AuthService-dev --since 5m --follow
   ```
   Look for "Invalid webhook signature" errors

### Messages Not Sending

1. **Check access token is valid:**
   ```bash
   curl -X GET "https://graph.facebook.com/v18.0/me?access_token=YOUR_ACCESS_TOKEN"
   ```

2. **Check phone number ID:**
   ```bash
   curl -X GET "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

3. **Test direct API call:**
   ```bash
   curl -X POST "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "messaging_product": "whatsapp",
       "to": "2348012345678",
       "type": "text",
       "text": {"body": "Test from TrustGuard"}
     }'
   ```

---

## Production Deployment Checklist

- [ ] Use production WhatsApp Business Number (not test number)
- [ ] Generate long-lived access tokens (via OAuth flow)
- [ ] Store tokens in Secrets Manager (not .env)
- [ ] Enable webhook signature verification
- [ ] Set up CloudWatch alarms for webhook failures
- [ ] Configure SNS notifications for CEO escalations
- [ ] Test end-to-end buyer flow
- [ ] Set up Meta Business Verification
- [ ] Apply for WhatsApp Business API approval (if needed)
- [ ] Configure rate limiting for webhooks

---

## Next Steps

After Meta integration is working:

1. **Implement chatbot conversation flows** (in `chatbot_router.py`)
2. **Add order confirmation via chat** (buyer confirms orders)
3. **Receipt upload via image messages** (buyer uploads bank receipt photos)
4. **CEO dashboard for OAuth management** (frontend integration)

---

## Support Resources

- [WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Instagram Messaging API Docs](https://developers.facebook.com/docs/messenger-platform/instagram)
- [Meta Webhook Reference](https://developers.facebook.com/docs/graph-api/webhooks)
- [TrustGuard Deployment Docs](../README.md)
