# 🔐 Meta OAuth & Credentials Configuration Guide

**For TrustGuard Dissertation Project**

---

## 📋 OAuth Redirect URL Setup

### Step 1: Configure Redirect URLs in Meta Developer Console

1. Go to: https://developers.facebook.com/apps
2. Select your app (or create one if you haven't)
3. Go to **Settings** → **Basic**
4. Scroll to **"App Domains"**
   - Add: `localhost`
   - Add: `trustguard.vercel.app` (for production)

5. Go to **Facebook Login** → **Settings**
6. Add these **Valid OAuth Redirect URIs:**

```
http://localhost:3001/ceo/oauth/meta/callback
http://localhost:8000/ceo/oauth/meta/callback
https://trustguard.vercel.app/ceo/oauth/meta/callback
```

7. **Save Changes**

---

## 🎯 What Redirect URL Does

The OAuth redirect URL is where Meta sends the CEO after they authorize TrustGuard to access their WhatsApp/Instagram:

**Flow:**
1. CEO clicks "Connect WhatsApp" in dashboard
2. Redirects to Meta login
3. CEO authorizes TrustGuard app
4. Meta redirects back to: `http://localhost:3001/ceo/oauth/meta/callback?code=ABC123`
5. Backend exchanges `code` for long-lived access token
6. Token stored in database for that CEO

---

## 📝 How to Provide Your Credentials

### **Method 1: Interactive Script (Easiest)**

Run this in your terminal:

```bash
cd "/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce"

./configure_meta.sh
```

The script will:
- Check existing credentials
- Prompt for missing ones
- Save securely to `.env`
- Validate configuration

---

### **Method 2: Manual .env Edit**

Edit the file directly:

```bash
cd backend
nano .env
```

Add these lines:

```bash
# Meta App (from developers.facebook.com → Your App → Settings → Basic)
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here

# Webhook Security (create a random string)
META_WEBHOOK_VERIFY_TOKEN=trustguard_verify_2025_random_string

# WhatsApp (from Your App → WhatsApp → Getting Started)
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_temporary_or_permanent_token

# Instagram (from Your App → Instagram → Getting Started)
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id
INSTAGRAM_PAGE_ID=your_facebook_page_id
INSTAGRAM_ACCESS_TOKEN=your_token_same_as_whatsapp_or_different
```

**Save and close:** Ctrl+X → Y → Enter

---

### **Method 3: Paste Here (I'll Create .env for you)**

Just paste your credentials here in this chat like:

```
META_APP_ID=123456789
META_APP_SECRET=abc123def456
WHATSAPP_PHONE_NUMBER_ID=987654321
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx...
```

I'll create the `.env` file for you!

---

## 🔍 Where to Find Each Credential

### 1. META_APP_ID & META_APP_SECRET

**Location:** https://developers.facebook.com/apps
- Select your app
- Go to **Settings** → **Basic**
- Copy **App ID**
- Click **Show** next to **App Secret** → Copy it

---

### 2. WHATSAPP Credentials

**Location:** https://developers.facebook.com/apps
- Select your app
- Click **WhatsApp** in left sidebar
- Go to **Getting Started**

You'll see:
- **Phone Number ID** → Copy this
- **WhatsApp Business Account ID** → Copy this

**For Access Token:**
- Click **System Users** (or create one)
- Generate token with permissions:
  - `whatsapp_business_management`
  - `whatsapp_business_messaging`
- Copy the token (shown only once!)

---

### 3. INSTAGRAM Credentials

**Location:** https://developers.facebook.com/apps
- Select your app
- Click **Instagram** in left sidebar
- Go to **Getting Started**

**Connect Instagram Business Account:**
1. Link your Instagram to a Facebook Page
2. Copy **Instagram Account ID**
3. Copy **Facebook Page ID**
4. Use same access token as WhatsApp (or generate separate)

---

### 4. WEBHOOK_VERIFY_TOKEN

**This is just a random string you create!**

Generate one:
```bash
openssl rand -hex 32
```

Or use anything like: `trustguard_webhook_secret_2025`

You'll use this when configuring webhooks in Meta Dashboard.

---

## ✅ After Configuration

### Test Your Setup:

```bash
# Test API connection
python3 test_meta_api.py

# Expected output:
# ✅ WhatsApp API: Connected successfully
# ✅ Instagram API: Connected successfully
```

---

## 🌐 Webhook Configuration (Next Step)

After credentials are set, you'll need to:

1. **Start ngrok:**
   ```bash
   ngrok http 8000
   ```

2. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

3. **Configure in Meta Dashboard:**

   **WhatsApp:**
   - Go to WhatsApp → Configuration
   - Callback URL: `https://abc123.ngrok.io/integrations/webhook/whatsapp`
   - Verify Token: (the one you set in .env)
   - Subscribe to: `messages`

   **Instagram:**
   - Go to Instagram → Configuration
   - Callback URL: `https://abc123.ngrok.io/integrations/webhook/instagram`
   - Verify Token: (same or different)
   - Subscribe to: `messages`, `messaging_postbacks`

4. **Click "Verify and Save"**

---

## 🚨 Important Notes

### Business Verification
- **Not required for development/testing**
- **Not required for dissertation**
- You can test with up to 5 phone numbers without verification
- For production launch, you'd need CAC/business documents

### Token Types
- **Temporary tokens:** Expire in 24 hours (good for testing)
- **Permanent tokens:** From System User (recommended)
- **User tokens:** Expire, need refresh (not recommended)

### Security
- Never commit `.env` to git (already in `.gitignore`)
- Keep tokens secret
- Regenerate if accidentally exposed

---

## 🎯 Quick Start Summary

1. **Set Redirect URL** in Meta Dashboard → Settings → Basic
2. **Run:** `./configure_meta.sh` OR edit `.env` manually
3. **Test:** `python3 test_meta_api.py`
4. **Start ngrok:** `ngrok http 8000`
5. **Configure webhooks** in Meta Dashboard
6. **Restart backend:** `cd backend && uvicorn app:app --reload`
7. **Test:** Send WhatsApp message to your business number

---

## 💬 How to Share Credentials with Me

**Option A: Run the script and let it handle everything**
```bash
./configure_meta.sh
```

**Option B: Paste them here in chat like:**
```
I have these credentials:
META_APP_ID: 123456
META_APP_SECRET: abc123
WHATSAPP_PHONE_NUMBER_ID: 789
WHATSAPP_ACCESS_TOKEN: EAAxxxx
```

I'll create the `.env` file for you!

---

**Ready? Share your credentials any way you prefer!** 🚀
