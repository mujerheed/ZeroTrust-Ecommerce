# 🎯 Meta API Quick Reference Card

## 📋 Setup Checklist

### Phase 1: Meta Developer Console (15-30 minutes)
- [ ] Create Meta Business Account at https://business.facebook.com
- [ ] Create Meta Developer Account at https://developers.facebook.com
- [ ] Create new Meta App (Type: "Business")
- [ ] Add WhatsApp product to app
- [ ] Add Instagram product to app
- [ ] Create System User for permanent tokens
- [ ] Generate access tokens with correct permissions

### Phase 2: Local Configuration (5 minutes)
- [ ] Run: `./setup_meta_api.sh` (interactive setup)
- [ ] Or manually edit `.env` with credentials
- [ ] Run: `python3 test_meta_api.py` (verify connection)
- [ ] Install ngrok: `sudo snap install ngrok`

### Phase 3: Webhook Setup (10 minutes)
- [ ] Start ngrok: `ngrok http 8000`
- [ ] Copy HTTPS URL (e.g., `https://abc123.ngrok.io`)
- [ ] Configure WhatsApp webhook in Meta Dashboard
- [ ] Configure Instagram webhook in Meta Dashboard
- [ ] Verify webhooks are receiving

### Phase 4: Testing (10 minutes)
- [ ] Send WhatsApp message to business number
- [ ] Send Instagram DM to business account
- [ ] Check logs: `tail -f /tmp/backend.log | grep WEBHOOK`
- [ ] Verify buyer OTP flow works end-to-end

---

## 🔑 Required Credentials

```bash
# Meta App
META_APP_ID=                        # From App Dashboard
META_APP_SECRET=                    # From App Settings
META_WEBHOOK_VERIFY_TOKEN=          # Random string you create

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=           # From WhatsApp > Getting Started
WHATSAPP_BUSINESS_ACCOUNT_ID=       # From WhatsApp > Getting Started
WHATSAPP_ACCESS_TOKEN=              # System User permanent token

# Instagram Messaging API
INSTAGRAM_ACCOUNT_ID=               # From Instagram > Getting Started
INSTAGRAM_PAGE_ID=                  # Facebook Page connected to Instagram
INSTAGRAM_ACCESS_TOKEN=             # Same as WhatsApp or separate
```

---

## 🚀 Quick Commands

```bash
# 1. Configure Meta API credentials
./setup_meta_api.sh

# 2. Test connection
python3 test_meta_api.py

# 3. Start ngrok tunnel
ngrok http 8000

# 4. Restart backend (after adding credentials)
cd backend
source venv/bin/activate
uvicorn app:app --reload

# 5. Monitor webhooks
tail -f /tmp/backend.log | grep WEBHOOK

# 6. Test Meta API directly (Python)
python3 -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()

url = f'https://graph.facebook.com/v18.0/{os.getenv(\"WHATSAPP_PHONE_NUMBER_ID\")}'
headers = {'Authorization': f'Bearer {os.getenv(\"WHATSAPP_ACCESS_TOKEN\")}'}
print(requests.get(url, headers=headers).json())
"
```

---

## 📱 Webhook URLs

```
# Development (ngrok)
WhatsApp:  https://YOUR_NGROK_URL/integrations/webhook/whatsapp
Instagram: https://YOUR_NGROK_URL/integrations/webhook/instagram

# Production (AWS)
WhatsApp:  https://api.trustguard.com/integrations/webhook/whatsapp
Instagram: https://api.trustguard.com/integrations/webhook/instagram
```

---

## 🔍 Troubleshooting

### ❌ "Invalid OAuth access token"
**Fix:** Regenerate token from System User with correct permissions

### ❌ Webhook not receiving messages
**Fix:** 
1. Check ngrok is running: `curl http://localhost:4040/api/tunnels`
2. Verify webhook URL in Meta Dashboard matches ngrok URL
3. Ensure backend is running: `ps aux | grep uvicorn`

### ❌ "Webhook verification failed"
**Fix:** Ensure `META_WEBHOOK_VERIFY_TOKEN` in `.env` matches Meta Dashboard

### ❌ "Signature validation failed"
**Fix:** Ensure `META_APP_SECRET` is correct in `.env`

---

## 📊 Testing Buyer Flow

### WhatsApp Flow:
1. **Buyer sends:** "Hello" to business number
2. **Bot responds:** "Welcome to TrustGuard! Please verify..."
3. **Bot sends OTP:** 8-character code (e.g., `aB3$xY7!`)
4. **Buyer replies:** with OTP
5. **Bot verifies:** "✅ Verified! You can now place orders"

### Instagram Flow:
1. **Buyer DMs:** Instagram business account
2. **Bot responds:** "Hi! Let's verify your account..."
3. **Bot sends OTP:** 8-character code
4. **Buyer replies:** with OTP
5. **Bot verifies:** Success message

---

## 🎯 Verification Checklist

After setup, verify:

- [ ] `test_meta_api.py` shows all ✅ passed
- [ ] ngrok tunnel is active and HTTPS URL copied
- [ ] Webhook URLs configured in Meta Dashboard
- [ ] Backend logs show "WhatsApp webhook verified successfully"
- [ ] Backend logs show "Instagram webhook verified successfully"
- [ ] Test message sent via WhatsApp received in logs
- [ ] Test message sent via Instagram received in logs
- [ ] Buyer OTP flow works end-to-end

---

## 📚 Documentation Files

1. **META_API_SETUP_GUIDE.md** - Comprehensive step-by-step guide
2. **setup_meta_api.sh** - Interactive credential setup script
3. **test_meta_api.py** - API connection test suite
4. **TESTING_CHECKLIST.md** - Complete testing checklist

---

## 🔗 Helpful Links

- **Meta Business Suite:** https://business.facebook.com
- **Meta Developers:** https://developers.facebook.com
- **WhatsApp API Docs:** https://developers.facebook.com/docs/whatsapp
- **Instagram API Docs:** https://developers.facebook.com/docs/messenger-platform
- **ngrok Dashboard:** http://localhost:4040 (when running)
- **System User Setup:** https://developers.facebook.com/docs/development/build-and-test/app-modes#system-users

---

## ⏱️ Estimated Time

| Task | Time |
|------|------|
| Meta Business Account setup | 10 min |
| Meta App creation | 5 min |
| WhatsApp/Instagram product setup | 10 min |
| System User & token generation | 10 min |
| Local configuration (`setup_meta_api.sh`) | 5 min |
| ngrok setup | 5 min |
| Webhook configuration | 5 min |
| Testing | 10 min |
| **Total** | **60 min** |

---

**🎉 You're all set! TrustGuard can now receive WhatsApp & Instagram messages!**
