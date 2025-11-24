# TrustGuard Deployment & Testing Guide

## ✅ Completed Features

### 1. **Multi-Role Authentication**
- ✅ Separate token storage (`vendor_token`, `ceo_token`)
- ✅ Separate session timers (60-minute auto-logout)
- ✅ OTP auto-validation (no button click needed)
- ✅ OTP password masking (shows `••••••`)
- ✅ Auto-verification on first login

### 2. **Dashboard & Analytics**
- ✅ Real-time data from backend APIs
- ✅ Order statistics and charts
- ✅ Notifications system
- ✅ Vendor preferences (graceful fallback)

### 3. **Receipt Verification**
- ✅ Textract OCR integration
- ✅ Checksum/hash display
- ✅ Amount mismatch warnings
- ✅ Confidence score badges
- ✅ Manual verification workflow

---

## 🧪 Local Testing (Current Status)

### Prerequisites
```bash
# Backend running
cd backend && ./venv/bin/uvicorn app:app --reload --port 8000

# Frontend running
cd frontend && npm run dev
# Access: http://localhost:3001
```

### Test Scenarios

#### 1. **Multi-Role Login Test**
```
Tab 1: CEO Login
- Go to http://localhost:3001/ceo/login
- Email: wadip30466@aikunkun.com (or phone: +2348133336318)
- Enter OTP from backend terminal (look for 🔑 emoji)
- Verify: Dashboard loads, session timer shows

Tab 2: Vendor Login (same browser)
- Go to http://localhost:3001/vendor/login
- Phone: +2348087654321 (or check DynamoDB for vendors)
- Enter OTP (auto-submits when complete)
- Verify: Both tabs stay logged in independently

Test:
✓ Both dashboards work simultaneously
✓ Logout from one doesn't affect the other
✓ Session timers are separate
✓ No token conflicts
```

#### 2. **OTP Features Test**
```
Expected Behavior:
✓ OTP shows as ••••••••• (masked)
✓ Auto-submits when all digits entered
✓ No "Verify" button click needed
✓ Vendor: 8 characters
✓ CEO: 6 characters
```

---

## 📱 WhatsApp/Instagram Bot Setup (Next Step)

### Meta Business Setup Required

#### 1. **WhatsApp Business API**
```bash
# Steps:
1. Create Meta Business Account: https://business.facebook.com
2. Create App → Business → WhatsApp
3. Get Phone Number ID
4. Generate Access Token (long-lived)
5. Configure Webhook URL (for receiving messages)

# Add to .env:
WHATSAPP_ACCESS_TOKEN=<your-token>
WHATSAPP_PHONE_NUMBER_ID=<your-phone-id>
WHATSAPP_VERIFY_TOKEN=<random-secret>
```

#### 2. **Instagram Messaging API**
```bash
# Steps:
1. Same Meta Business Account
2. Connect Instagram Professional account
3. Get Instagram ID
4. Generate Access Token
5. Configure Webhook URL

# Add to .env:
INSTAGRAM_ACCESS_TOKEN=<your-token>
INSTAGRAM_USER_ID=<your-ig-user-id>
```

#### 3. **Webhook Configuration**
```bash
# Your webhook URL (use ngrok for local testing):
ngrok http 8000

# Meta Webhook URLs:
WhatsApp: https://<your-domain>/auth/webhook/whatsapp
Instagram: https://<your-domain>/auth/webhook/instagram

# Webhook verification:
- Verify Token: <your-secret>
- Subscribe to: messages, messaging_postbacks
```

---

## 🤖 Testing Bot Interaction (Local)

### Option 1: Use Mock API (No Meta Credentials)
```bash
# Backend has mock API for testing
# File: backend/integrations/mock_api/

# Simulate buyer message:
curl -X POST http://localhost:8000/auth/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "2348012345678",
            "type": "text",
            "text": {"body": "Hello"}
          }]
        }
      }]
    }]
  }'
```

### Option 2: Real Meta Testing (With Credentials)
```bash
# 1. Set up ngrok
ngrok http 8000
# Copy HTTPS URL: https://abc123.ngrok.io

# 2. Configure Meta webhooks
WhatsApp Webhook: https://abc123.ngrok.io/auth/webhook/whatsapp
Instagram Webhook: https://abc123.ngrok.io/auth/webhook/instagram

# 3. Test via actual WhatsApp/Instagram
- Message your WhatsApp Business number
- Bot should respond with OTP
- Complete buyer registration flow
```

---

## 🔄 Complete E2E Flow Test

### Buyer → Vendor → CEO

```
1. BUYER (WhatsApp/Instagram):
   - Send "Hello" to bot
   - Receive welcome message
   - Request OTP
   - Verify with OTP
   - Create order
   - Upload receipt image

2. VENDOR (Dashboard):
   - Login at /vendor/login
   - View new order in /vendor/orders
   - See receipt in /vendor/receipts
   - Review OCR data
   - Approve or flag receipt

3. CEO (Dashboard):
   - Login at /ceo/login
   - View all vendors in /ceo/vendors
   - Check flagged orders in /ceo/approvals
   - Approve high-value transactions
   - View audit logs
```

---

## 🚀 AWS Production Deployment

### Backend (AWS Lambda + API Gateway)

```bash
# 1. Install AWS SAM CLI
brew install aws-sam-cli  # macOS
# or: pip install aws-sam-cli

# 2. Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)

# 3. Build SAM template
cd infrastructure/cloudformation
sam build

# 4. Deploy to AWS
sam deploy --guided

# Follow prompts:
- Stack Name: trustguard-prod
- AWS Region: us-east-1
- Confirm changes: y
- Allow SAM CLI IAM role creation: y
- Save arguments to config: y

# 5. Get API Gateway URL
aws cloudformation describe-stacks \
  --stack-name trustguard-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text

# Example output: https://xyz123.execute-api.us-east-1.amazonaws.com/Prod
```

### Frontend (Vercel)

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy from frontend directory
cd frontend
vercel

# Follow prompts:
- Set up and deploy: y
- Which scope: <your-account>
- Link to existing project: n
- Project name: trustguard-frontend
- Directory: ./
- Build command: npm run build
- Output directory: .next
- Development command: npm run dev

# 3. Configure environment variables in Vercel dashboard:
NEXT_PUBLIC_API_URL=https://xyz123.execute-api.us-east-1.amazonaws.com/Prod
```

### Post-Deployment Configuration

```bash
# 1. Update Meta Webhook URLs (Production)
WhatsApp: https://xyz123.execute-api.us-east-1.amazonaws.com/Prod/auth/webhook/whatsapp
Instagram: https://xyz123.execute-api.us-east-1.amazonaws.com/Prod/auth/webhook/instagram

# 2. Add Production Secrets to AWS Secrets Manager
aws secretsmanager create-secret \
  --name TrustGuard-WhatsApp-Token \
  --secret-string '{"token":"<your-whatsapp-token>"}'

aws secretsmanager create-secret \
  --name TrustGuard-Instagram-Token \
  --secret-string '{"token":"<your-instagram-token>"}'

# 3. Verify DynamoDB Tables Created
aws dynamodb list-tables | grep TrustGuard

# Expected:
# - TrustGuard-Users
# - TrustGuard-OTPs
# - TrustGuard-Orders
# - TrustGuard-Receipts
# - TrustGuard-AuditLogs

# 4. Test Production Endpoint
curl https://xyz123.execute-api.us-east-1.amazonaws.com/Prod/vendor/dashboard \
  -H "Authorization: Bearer <token>"
```

---

## 🐛 Troubleshooting

### OTP Not Working
```bash
# Check backend logs
tail -f /tmp/backend.log | grep OTP

# Verify DynamoDB OTPs table
aws dynamodb scan --table-name TrustGuard-OTPs-dev --max-items 5
```

### Multi-Role Login Issues
```bash
# Check browser localStorage
- F12 → Application → Local Storage
- Should see: vendor_token, ceo_token, vendor_session_start, ceo_session_start

# Clear and retry
localStorage.clear()
```

### WhatsApp Bot Not Responding
```bash
# 1. Check webhook verification
curl https://your-domain.com/auth/webhook/whatsapp?hub.verify_token=<token>&hub.challenge=test

# 2. Check Meta App Dashboard
- Webhooks subscribed?
- Phone number verified?
- Access token valid?

# 3. Test with mock data
curl -X POST http://localhost:8000/auth/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d @backend/integrations/mock_api/whatsapp_message_mock.json
```

---

## 📊 Monitoring & Logs

### AWS CloudWatch (Production)
```bash
# View Lambda logs
aws logs tail /aws/lambda/AuthServiceLambda --follow

# View API Gateway logs
aws logs tail /aws/apigateway/<api-id> --follow
```

### Local Development
```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
# Check browser console (F12)
```

---

## 🎯 Success Criteria

### ✅ All Features Working
- [ ] CEO can create vendors
- [ ] Vendor can login and see dashboard
- [ ] Buyer can send message to WhatsApp/Instagram bot
- [ ] Buyer receives OTP and can verify
- [ ] Buyer can create order
- [ ] Buyer can upload receipt
- [ ] Vendor sees receipt and can approve/reject
- [ ] High-value orders escalate to CEO
- [ ] CEO can approve flagged transactions
- [ ] All sessions work independently
- [ ] Audit logs capture all actions

---

## 📞 Support

Issues? Check:
1. Backend logs: `tail -f /tmp/backend.log`
2. Frontend console: Browser DevTools (F12)
3. DynamoDB tables: AWS Console or `aws dynamodb scan`
4. Meta Developer Dashboard: App status and webhooks

---

**Next Step**: Test multi-role login locally, then set up Meta credentials for bot testing!
