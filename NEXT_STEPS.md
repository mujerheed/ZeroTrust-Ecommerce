# 🚀 Next Steps - Meta API Integration

**Status:** ✅ WhatsApp API Connected! Instagram ready to test.

---

## ✅ What's Working

- **WhatsApp Business API:** Connected (200 OK)
- **Phone Number:** +1 (555) 633-7144 (Test Number)
- **Quality Rating:** UNKNOWN (new account - normal)
- **Credentials:** Saved to `backend/.env`

---

## 📋 Next Steps (In Order)

### Step 1: Install and Start ngrok 🌐

ngrok creates an HTTPS tunnel to your local backend so Meta can send webhooks.

```bash
# Install ngrok (if not already installed)
sudo snap install ngrok

# Start tunnel to your backend (port 8000)
ngrok http 8000

# ⚠️ KEEP THIS TERMINAL OPEN - Copy the HTTPS URL
# Example: https://abc123.ngrok.io
```

**You'll see:**
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Copy that HTTPS URL** - you'll need it for Step 2!

---

### Step 2: Configure Webhooks in Meta Developer Console 🔗

**Go to:** [Meta Developer Console](https://developers.facebook.com/apps)

#### For WhatsApp:
1. Click your app → **WhatsApp** → **Configuration**
2. Click **Edit** next to "Webhook"
3. Enter:
   - **Callback URL:** `https://YOUR-NGROK-URL.ngrok.io/integrations/webhook/whatsapp`
   - **Verify Token:** `test_trustgu@rd_25`
4. Click **Verify and Save**
5. Subscribe to **messages** event

#### For Instagram:
1. Click your app → **Messenger** → **Configuration**
2. Click **Edit** next to "Webhook"
3. Enter:
   - **Callback URL:** `https://YOUR-NGROK-URL.ngrok.io/integrations/webhook/instagram`
   - **Verify Token:** `test_trustgu@rd_25`
4. Click **Verify and Save**
5. Subscribe to **messages** event

**Expected:** ✅ Green checkmark next to webhook URL

---

### Step 3: Restart Backend to Load New Credentials 🔄

Your backend needs to reload the `.env` file with Meta credentials:

```bash
# Kill current backend process
pkill -f "uvicorn backend.app:app"

# Navigate to backend
cd backend

# Restart with new environment variables
uvicorn app:app --reload --port 8000

# ✅ You should see: "Application startup complete"
```

---

### Step 4: Test End-to-End Buyer Flow 📱

#### Option A: WhatsApp Test
1. Open WhatsApp
2. Send message to: **+1 (555) 633-7144**
3. Type: `Hello`

**Expected Response:**
```
Welcome to TrustGuard! 🛡️
Your OTP is: ABC12#@5
Reply with this code to verify.
```

#### Option B: Instagram Test
1. Open Instagram
2. Find your business page
3. Send DM: `Hello`

**Expected:** Same OTP response

---

### Step 5: Check Backend Logs 📊

In a new terminal:

```bash
# Watch webhook activity
tail -f backend/logs/app.log | grep WEBHOOK

# Or check recent logs
cat backend/logs/app.log | tail -50
```

**What to Look For:**
```
✅ WEBHOOK received: WhatsApp message from wa_1234567890
✅ OTP sent: ABC12#@5
✅ Buyer verified: buyer_123
```

---

## 🔍 Troubleshooting

### Webhook Verification Failed
- **Check:** ngrok is running and HTTPS URL is correct
- **Check:** Verify token exactly matches: `test_trustgu@rd_25`
- **Check:** Backend is running on port 8000

### No Message Received
- **Check:** Phone number is correct (+1 555-633-7144)
- **Check:** Webhook subscribed to "messages" event
- **Check:** ngrok terminal shows incoming requests

### Backend Not Responding
- **Check:** Backend restarted after adding credentials
- **Check:** `.env` file has all Meta credentials
- **Run:** `cd backend && cat .env | grep WHATSAPP`

---

## 📱 What Happens Next?

After webhooks work:

1. **Buyer sends message** → Webhook triggers
2. **Backend generates OTP** → Sends via WhatsApp/Instagram
3. **Buyer replies with OTP** → Backend verifies
4. **Buyer creates order** → Uploads receipt
5. **Vendor reviews** → Approves or flags
6. **CEO approves** (if high-value) → Order complete

---

## 🎯 Your Current Status

```
✅ Meta App Created
✅ WhatsApp Business API Connected
✅ Instagram Messaging API Connected
✅ Credentials Configured in .env
✅ Phone Number Verified (+1 555-633-7144)
⏳ ngrok Setup → YOU ARE HERE
⏳ Webhook Configuration
⏳ End-to-End Test
⏳ Production Deployment
```

---

## 🚨 Important Notes

### For Dissertation Testing:
- ✅ No business verification needed (CAC not required)
- ✅ Up to 5 test phone numbers allowed
- ✅ Full messaging API access
- ⚠️ Production would need business verification

### Token Expiry:
- Your access token is **long-lived** (60 days)
- If it expires, regenerate from Meta Business Suite
- Update in `.env` and restart backend

### Rate Limits:
- Test accounts: 1000 messages/day
- Quality rating improves with usage
- Current: UNKNOWN (new account - normal)

---

## 📞 Need Help?

**Quick Commands:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Test WhatsApp API directly
python3 test_meta_api.py

# View all Meta credentials
cat backend/.env | grep -E "^(WHATSAPP|INSTAGRAM|META_WEBHOOK)"

# Restart everything
pkill -f uvicorn && cd backend && uvicorn app:app --reload
```

**Documentation:**
- `META_API_SETUP_GUIDE.md` - Complete setup
- `META_QUICK_REFERENCE.md` - Quick commands
- `META_CREDENTIALS_GUIDE.md` - Credential help

---

**Ready to proceed?** Start with Step 1 (ngrok) and let me know when you have the HTTPS URL!
