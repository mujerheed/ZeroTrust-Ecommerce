# 🚀 Meta API Setup Guide (WhatsApp & Instagram)

**TrustGuard Zero Trust E-commerce Platform**  
**Date:** November 23, 2025

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Meta Business Account Setup](#meta-business-account-setup)
3. [WhatsApp Business API Setup](#whatsapp-business-api-setup)
4. [Instagram Messaging API Setup](#instagram-messaging-api-setup)
5. [Webhook Configuration](#webhook-configuration)
6. [Testing with ngrok](#testing-with-ngrok)
7. [Environment Variables](#environment-variables)
8. [Verification & Testing](#verification--testing)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

Before starting, ensure you have:

- [ ] Meta (Facebook) Business Account
- [ ] Meta Developer Account (https://developers.facebook.com)
- [ ] Business phone number for WhatsApp (not your personal number)
- [ ] Instagram Business Account connected to Facebook Page
- [ ] Valid government-issued ID (for business verification)
- [ ] Business website or email domain
- [ ] Credit card (for Meta verification, may not be charged)

**Tools Required:**
```bash
# Install ngrok for local webhook testing
sudo snap install ngrok

# Or download from: https://ngrok.com/download
```

---

## 🏢 Meta Business Account Setup

### Step 1: Create Meta Business Account

1. **Go to:** https://business.facebook.com
2. **Click:** "Create Account"
3. **Fill in:**
   - Business name (e.g., "TrustGuard Nigeria")
   - Your name
   - Business email
4. **Verify email** and complete setup

### Step 2: Business Verification (Required for Production)

1. **Navigate to:** Business Settings → Security Center
2. **Click:** "Start Verification"
3. **Choose verification method:**
   - Phone number
   - Business documents (CAC registration in Nigeria)
   - Domain verification
4. **Submit documents** and wait for approval (1-3 business days)

---

## 📱 WhatsApp Business API Setup

### Step 1: Create Meta App

1. **Go to:** https://developers.facebook.com/apps
2. **Click:** "Create App"
3. **Select:** "Business" type
4. **Fill in:**
   - App name: "TrustGuard Bot"
   - App contact email: your email
   - Business account: Select your business
5. **Click:** "Create App"

### Step 2: Add WhatsApp Product

1. **In your app dashboard:**
   - Scroll to "Add Products"
   - Find "WhatsApp" → Click "Set Up"
2. **Select or create** WhatsApp Business Account
3. **Add phone number:**
   - Must be a number you can receive SMS/calls on
   - Cannot be already registered on WhatsApp
   - Recommended: Get a new business number

### Step 3: Get WhatsApp Credentials

1. **Navigate to:** WhatsApp → Getting Started
2. **Copy these values:**
   ```
   WHATSAPP_PHONE_NUMBER_ID=<your_phone_number_id>
   WHATSAPP_BUSINESS_ACCOUNT_ID=<your_business_account_id>
   ```

3. **Generate Access Token:**
   - Go to: WhatsApp → API Setup
   - Click: "Generate Access Token"
   - **Temporary Token (24 hours):** For testing
   - **Permanent Token:** Follow System User setup below

### Step 4: Create System User (Permanent Token)

1. **Navigate to:** Business Settings → Users → System Users
2. **Click:** "Add System User"
   - Name: "TrustGuard Production Bot"
   - Role: Admin
3. **Generate Token:**
   - Click on the system user
   - Click "Generate New Token"
   - **Select App:** TrustGuard Bot
   - **Permissions:** Check all WhatsApp permissions:
     - `whatsapp_business_management`
     - `whatsapp_business_messaging`
   - **Token Expires:** Never (for production)
   - **Copy token** immediately (shown only once!)

4. **Assign Assets:**
   - Click "Assign Assets"
   - Select WhatsApp Business Account
   - Give "Full Control"

**Save this token securely:**
```bash
WHATSAPP_ACCESS_TOKEN=<your_permanent_access_token>
```

### Step 5: Configure Webhook

1. **Navigate to:** WhatsApp → Configuration
2. **Webhook URL:** (will set up with ngrok later)
3. **Verify Token:** Create a random string
   ```bash
   # Generate secure verify token
   openssl rand -hex 32
   ```
   Save as:
   ```
   WHATSAPP_VERIFY_TOKEN=<your_generated_token>
   ```

4. **Webhook Fields:** Subscribe to:
   - `messages` ✅
   - `message_template_status_update` ✅

---

## 📸 Instagram Messaging API Setup

### Step 1: Connect Instagram Account

1. **In Meta App Dashboard:**
   - Add Product → Instagram
   - Click "Set Up"

2. **Connect Instagram Account:**
   - Must be Instagram Business Account
   - Must be linked to a Facebook Page
   - Click "Add Account"
   - Login and authorize

### Step 2: Get Instagram Credentials

1. **Navigate to:** Instagram → Getting Started
2. **Copy these values:**
   ```
   INSTAGRAM_ACCOUNT_ID=<your_instagram_account_id>
   INSTAGRAM_PAGE_ID=<your_facebook_page_id>
   ```

3. **Access Token:**
   - Instagram uses the same access token as WhatsApp
   - Use the System User token created earlier

### Step 3: Configure Instagram Webhook

1. **Navigate to:** Instagram → Configuration
2. **Webhook URL:** (same as WhatsApp)
3. **Verify Token:** Can use same token as WhatsApp
   ```
   INSTAGRAM_VERIFY_TOKEN=<same_as_whatsapp_or_different>
   ```

4. **Webhook Fields:** Subscribe to:
   - `messages` ✅
   - `messaging_postbacks` ✅
   - `messaging_optins` ✅

---

## 🔗 Webhook Configuration

### Step 1: Set Up ngrok for Local Testing

```bash
# Start ngrok tunnel
ngrok http 8000

# Output will show:
# Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Step 2: Configure Webhook URLs

**For WhatsApp:**
1. Go to: WhatsApp → Configuration
2. **Callback URL:** `https://abc123.ngrok.io/integrations/webhook/whatsapp`
3. **Verify Token:** (the one you generated earlier)
4. Click "Verify and Save"

**For Instagram:**
1. Go to: Instagram → Configuration  
2. **Callback URL:** `https://abc123.ngrok.io/integrations/webhook/instagram`
3. **Verify Token:** (same or different)
4. Click "Verify and Save"

### Step 3: Update Environment Variables

Create or update `.env` file in `backend/`:

```bash
# Meta App Credentials
META_APP_ID=<your_app_id>
META_APP_SECRET=<your_app_secret>

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=<your_phone_number_id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<your_business_account_id>
WHATSAPP_ACCESS_TOKEN=<your_permanent_access_token>
WHATSAPP_VERIFY_TOKEN=<your_verify_token>

# Instagram Messaging API
INSTAGRAM_ACCOUNT_ID=<your_instagram_account_id>
INSTAGRAM_PAGE_ID=<your_facebook_page_id>
INSTAGRAM_ACCESS_TOKEN=<same_as_whatsapp_or_different>
INSTAGRAM_VERIFY_TOKEN=<your_verify_token>

# Webhook Security
META_WEBHOOK_SECRET=<your_app_secret>
```

---

## 🔐 Environment Variables

### Update `backend/common/config.py`:

The config file should already have these settings. Verify:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Meta API
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    
    # WhatsApp
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    
    # Instagram
    INSTAGRAM_ACCOUNT_ID: str = ""
    INSTAGRAM_PAGE_ID: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_VERIFY_TOKEN: str = ""
    
    class Config:
        env_file = ".env"
```

---

## ✅ Verification & Testing

### Step 1: Test Webhook Verification

**Check ngrok requests:**
```bash
# In new terminal, monitor ngrok traffic
curl http://localhost:4040/api/requests
```

**Verify webhook is receiving:**
- Meta will send GET request to verify
- Check backend logs: `tail -f /tmp/backend.log`

### Step 2: Send Test Message

**WhatsApp Test:**
1. Save your WhatsApp Business number in your phone
2. Send a message: "Hello"
3. Check backend logs for incoming webhook
4. Should see: `[WEBHOOK] WhatsApp message received`

**Instagram Test:**
1. Go to your Instagram Business account
2. Send a DM from another account: "Hi"
3. Check backend logs
4. Should see: `[WEBHOOK] Instagram message received`

### Step 3: Test Buyer OTP Flow

**Complete flow test:**

```bash
# 1. Start ngrok
ngrok http 8000

# 2. Update webhook URLs in Meta dashboard

# 3. Send WhatsApp message
# From your phone to business number: "Hello"

# 4. Check logs - should see:
# - Buyer ID created: wa_<phone_number>
# - OTP generated: 8-character code
# - OTP sent via WhatsApp: "Your TrustGuard code is: ABC12@#$"

# 5. Reply with OTP
# Should see: "OTP verified! Welcome to TrustGuard"
```

---

## 🧪 Testing Script

Create a test script to verify Meta API connectivity:

```bash
cd backend
python3 << 'EOF'
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Test WhatsApp API
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')

url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}"
headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}

response = requests.get(url, headers=headers)
print(f"WhatsApp API Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test Instagram API
INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_ACCOUNT_ID')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')

url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}"
headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}

response = requests.get(url, headers=headers)
print(f"\nInstagram API Status: {response.status_code}")
print(f"Response: {response.json()}")
EOF
```

---

## 🐛 Troubleshooting

### Issue 1: Webhook Not Receiving Messages

**Check:**
- ngrok is running and HTTPS URL is correct
- Webhook URL matches exactly: `https://xxx.ngrok.io/integrations/webhook/whatsapp`
- Verify token matches in both Meta dashboard and `.env`
- Backend server is running: `ps aux | grep uvicorn`

**Debug:**
```bash
# Check ngrok requests
curl http://localhost:4040/api/requests | jq

# Check backend logs
tail -f /tmp/backend.log | grep WEBHOOK
```

### Issue 2: Invalid Access Token

**Error:** `Invalid OAuth access token`

**Fix:**
- Regenerate access token from System User
- Ensure token has correct permissions
- Check token hasn't expired (temporary tokens last 24 hours)

### Issue 3: Message Sending Failed

**Error:** `(#100) The parameter messaging_product is required`

**Fix:**
```python
# Ensure message payload includes messaging_product
{
    "messaging_product": "whatsapp",  # Required!
    "to": "+2348012345678",
    "type": "text",
    "text": {"body": "Your message"}
}
```

### Issue 4: ngrok URL Changes

**Problem:** ngrok generates new URL each time

**Solutions:**

**Option 1: ngrok Static Domain (Recommended)**
```bash
# Sign up for free ngrok account: https://dashboard.ngrok.com
ngrok config add-authtoken <your_token>

# Get static domain
ngrok http 8000 --domain=trustguard.ngrok.io
```

**Option 2: Update Webhook Programmatically**
```python
# Script to update webhook URL automatically
import requests
import os

def update_whatsapp_webhook(new_url):
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/subscribed_apps"
    # ... update webhook
```

---

## 📊 Monitoring & Logs

### Backend Logs

```bash
# Watch all webhook activity
tail -f /tmp/backend.log | grep -E "WEBHOOK|OTP|Meta"

# Watch specific platform
tail -f /tmp/backend.log | grep WhatsApp
tail -f /tmp/backend.log | grep Instagram
```

### ngrok Dashboard

Access: `http://localhost:4040`

**Features:**
- Live request inspection
- Replay requests
- Request/response headers
- Timing information

### Meta Webhook Logs

1. **Go to:** Meta App Dashboard
2. **Navigate to:** WhatsApp → Webhook or Instagram → Webhook
3. **Click:** "View Logs"
4. **See:** All webhook deliveries, errors, retries

---

## 🚀 Production Deployment

### When Moving to Production:

1. **Update webhook URLs** from ngrok to production:
   ```
   https://api.trustguard.com/integrations/webhook/whatsapp
   https://api.trustguard.com/integrations/webhook/instagram
   ```

2. **Store tokens in AWS Secrets Manager:**
   ```bash
   aws secretsmanager create-secret \
     --name TrustGuard-MetaTokens \
     --secret-string '{
       "whatsapp_access_token": "...",
       "instagram_access_token": "...",
       "app_secret": "..."
     }'
   ```

3. **Complete Business Verification:**
   - Required for production message limits
   - WhatsApp: 1,000 messages/day → Unlimited
   - Instagram: Similar limits

4. **Set up Message Templates** (WhatsApp):
   - Required for proactive messages
   - Submit templates for approval
   - Use for OTP delivery

---

## 📚 Additional Resources

- **WhatsApp Business API:** https://developers.facebook.com/docs/whatsapp
- **Instagram Messaging API:** https://developers.facebook.com/docs/messenger-platform
- **Webhook Setup:** https://developers.facebook.com/docs/graph-api/webhooks
- **Message Templates:** https://developers.facebook.com/docs/whatsapp/message-templates
- **ngrok Documentation:** https://ngrok.com/docs

---

## ✅ Setup Checklist

- [ ] Meta Business Account created
- [ ] Meta Developer Account created
- [ ] Meta App created ("TrustGuard Bot")
- [ ] WhatsApp Business Account added
- [ ] WhatsApp phone number registered
- [ ] System User created with permanent token
- [ ] WhatsApp webhook configured
- [ ] Instagram Business Account connected
- [ ] Instagram webhook configured
- [ ] ngrok installed and running
- [ ] Environment variables updated in `.env`
- [ ] Backend restarted with new env vars
- [ ] Webhook verification successful
- [ ] Test message sent via WhatsApp
- [ ] Test message sent via Instagram
- [ ] Buyer OTP flow tested end-to-end

---

**Setup Complete! 🎉**

Your TrustGuard platform is now ready to receive and respond to messages from WhatsApp and Instagram!

**Next:** Test the complete buyer journey from chat to order completion.
