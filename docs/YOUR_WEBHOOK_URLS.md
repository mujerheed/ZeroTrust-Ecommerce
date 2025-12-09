# Your TrustGuard Webhook URLs (AWS Deployment)

**Generated:** December 8, 2025  
**AWS Region:** us-east-1  
**Stack Name:** TrustGuard-Dev

---

## 🌐 Your API Gateway URL

```
https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/
```

---

## 📱 Meta Webhook Configuration

### WhatsApp Business API

**Callback URL:**
```
https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp
```

**Verify Token:**
```
trustguard_verify_2025
```

**Subscribe to Fields:**
- ✅ `messages`
- ✅ `messaging_postbacks` (optional)

---

### Instagram Messaging API

**Callback URL:**
```
https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/instagram
```

**Verify Token:**
```
trustguard_verify_2025
```

**Subscribe to Fields:**
- ✅ `messages`
- ✅ `messaging_postbacks` (optional)

---

## 🔧 How to Configure in Meta App Dashboard

### Step 1: Go to Meta App Settings
1. Visit [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Select your app (App ID: `850791007281950`)
3. Click **Webhooks** in the left sidebar

### Step 2: Configure WhatsApp Webhook
1. Find the **WhatsApp** section
2. Click **Edit** next to "Callback URL"
3. **Paste this URL:**
   ```
   https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp
   ```
4. **Verify Token:** `trustguard_verify_2025`
5. Click **Verify and Save**
6. ✅ Subscribe to `messages` field

### Step 3: Configure Instagram Webhook
1. Find the **Instagram** section
2. Click **Edit** next to "Callback URL"
3. **Paste this URL:**
   ```
   https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/instagram
   ```
4. **Verify Token:** `trustguard_verify_2025`
5. Click **Verify and Save**
6. ✅ Subscribe to `messages` field

---

## ✅ Testing Your Webhook

### Method 1: Meta Test Button (Recommended)
1. In Meta App Dashboard → Webhooks
2. Click **Test** button next to WhatsApp webhook
3. Select `messages` event
4. Click **Send to My Server**
5. **Expected Response:** `200 OK`

### Method 2: Check CloudWatch Logs
Since your backend is deployed to AWS Lambda, check CloudWatch for logs:

```bash
# View recent Lambda logs
aws logs tail /aws/lambda/TrustGuard-AuthFunction-dev --follow --region us-east-1
```

### Method 3: Real Message Test
1. **WhatsApp:**
   - Join sandbox: Send `join YOUR-CODE` to Meta's test number
   - Send message: `Hello TrustGuard`
   - Check CloudWatch logs

2. **Instagram:**
   - Send DM to your Instagram business account
   - Check CloudWatch logs

---

## 🔍 Troubleshooting

### Issue: "Webhook Verification Failed"

**Check 1: Correct Verify Token?**
- Your `.env` should have: `META_WEBHOOK_VERIFY_TOKEN=trustguard_verify_2025`
- Meta App Dashboard should use the same token

**Check 2: URL Includes /Prod/?**
- ✅ Correct: `https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp`
- ❌ Wrong: `https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/integrations/webhook/whatsapp` (missing /Prod/)

**Check 3: Lambda Function Deployed?**
```bash
# Check if Lambda is deployed
aws lambda get-function --function-name TrustGuard-AuthFunction-dev --region us-east-1
```

---

### Issue: "Test Shows Success But No Logs"

**Solution:** Check CloudWatch Logs (not local terminal)

Since your backend is on AWS Lambda, logs go to CloudWatch, not your local terminal.

**View Logs:**
```bash
# Install AWS CLI if not already installed
# Then run:
aws logs tail /aws/lambda/TrustGuard-AuthFunction-dev --follow --region us-east-1
```

Or use AWS Console:
1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Click **Log groups**
3. Find `/aws/lambda/TrustGuard-AuthFunction-dev`
4. View recent log streams

---

### Issue: "Signature Verification Failed"

**Check Meta App Secret:**
```bash
# Your Meta App Secret should be stored in AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id /TrustGuard/dev/meta \
  --region us-east-1 \
  --query SecretString \
  --output text
```

Expected format:
```json
{
  "APP_ID": "850791007281950",
  "APP_SECRET": "5ba4cd58e7205ecd439cf49ac11c7adb",
  "WEBHOOK_VERIFY_TOKEN": "trustguard_verify_2025"
}
```

---

## 📊 AWS Resources

| Resource | Value |
|----------|-------|
| **API Gateway** | `https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/` |
| **S3 Bucket** | `trustguard-receipts-605009361024-dev` |
| **KMS Key ID** | `a5f04e48-2f90-4dc8-a6e5-4924462fd8c8` |
| **App Secrets** | `arn:aws:secretsmanager:us-east-1:605009361024:secret:/TrustGuard/dev/app-TrustGuard-Dev-tyZYNr` |
| **Meta Secrets** | `arn:aws:secretsmanager:us-east-1:605009361024:secret:/TrustGuard/dev/meta-TrustGuard-Dev-q3dCdF` |
| **SNS Topic** | `arn:aws:sns:us-east-1:605009361024:TrustGuard-EscalationAlert-dev` |

---

## 🔐 Security Notes

1. **HTTPS Only:** Meta requires HTTPS webhooks (✅ API Gateway provides this)
2. **Signature Validation:** All webhooks are HMAC-verified using your App Secret
3. **Secrets Manager:** Sensitive credentials stored in AWS Secrets Manager (not in code)
4. **Encryption:** All data encrypted at rest (KMS) and in transit (TLS)

---

## 📝 Quick Copy-Paste

**WhatsApp Webhook URL:**
```
https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp
```

**Instagram Webhook URL:**
```
https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/instagram
```

**Verify Token:**
```
trustguard_verify_2025
```

---

**Last Updated:** December 8, 2025  
**Status:** ✅ AWS Deployment Active
