# CloudWatch Logs - Quick Reference

## Your Lambda Functions

| Service | Lambda Function Name | Log Group |
|---------|---------------------|-----------|
| **Auth** | `TrustGuard-AuthService-dev` | `/aws/lambda/TrustGuard-AuthService-dev` |
| **CEO** | `TrustGuard-CEOService-dev` | `/aws/lambda/TrustGuard-CEOService-dev` |
| **Vendor** | `TrustGuard-VendorService-dev` | `/aws/lambda/TrustGuard-VendorService-dev` |
| **Order** | `TrustGuard-OrderService-dev` | `/aws/lambda/TrustGuard-OrderService-dev` |
| **Receipt** | `TrustGuard-ReceiptService-dev` | `/aws/lambda/TrustGuard-ReceiptService-dev` |

---

## View Webhook Logs

### WhatsApp/Instagram Webhooks
Webhooks are handled by the **CEO Service** (integration routes):

```bash
# Follow webhook logs in real-time
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1

# View last 100 lines
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --region us-east-1

# Filter for webhook-specific logs
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1 --filter-pattern "webhook"
```

### Authentication Logs
```bash
# Follow auth logs (OTP, login, etc.)
aws logs tail /aws/lambda/TrustGuard-AuthService-dev --follow --region us-east-1
```

### Vendor Dashboard Logs
```bash
# Follow vendor service logs
aws logs tail /aws/lambda/TrustGuard-VendorService-dev --follow --region us-east-1
```

### Order Processing Logs
```bash
# Follow order service logs
aws logs tail /aws/lambda/TrustGuard-OrderService-dev --follow --region us-east-1
```

### Receipt Upload Logs
```bash
# Follow receipt service logs
aws logs tail /aws/lambda/TrustGuard-ReceiptService-dev --follow --region us-east-1
```

---

## View All Logs Together

To see logs from all services:

```bash
# Create a script to tail all logs
cat > tail_all_logs.sh << 'EOF'
#!/bin/bash
aws logs tail /aws/lambda/TrustGuard-AuthService-dev --follow --region us-east-1 &
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1 &
aws logs tail /aws/lambda/TrustGuard-VendorService-dev --follow --region us-east-1 &
aws logs tail /aws/lambda/TrustGuard-OrderService-dev --follow --region us-east-1 &
aws logs tail /aws/lambda/TrustGuard-ReceiptService-dev --follow --region us-east-1 &
wait
EOF

chmod +x tail_all_logs.sh
./tail_all_logs.sh
```

---

## Filter Logs by Pattern

### Find Errors
```bash
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1 --filter-pattern "ERROR"
```

### Find Webhook Requests
```bash
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1 --filter-pattern "WEBHOOK"
```

### Find Specific User Activity
```bash
aws logs tail /aws/lambda/TrustGuard-AuthService-dev --follow --region us-east-1 --filter-pattern "wa_234"
```

---

## View Logs in AWS Console

Alternative to CLI - use AWS Console:

1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Click **Log groups** in left sidebar
3. Click on a log group (e.g., `/aws/lambda/TrustGuard-CEOService-dev`)
4. Click on the latest log stream
5. View logs in real-time

**Direct Links:**
- [CEO Service Logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252FTrustGuard-CEOService-dev)
- [Auth Service Logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252FTrustGuard-AuthService-dev)

---

## Test Webhook and View Logs

### Step 1: Start Tailing Logs
```bash
# In one terminal, tail CEO service logs (webhooks)
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1
```

### Step 2: Send Test Webhook
```bash
# In another terminal, test the webhook
curl -X POST https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"object":"whatsapp_business_account"}'
```

### Step 3: Check Logs
You should see output like:
```
2025-12-08T05:34:12.123Z [INFO] Webhook received: POST /integrations/webhook/whatsapp
2025-12-08T05:34:12.456Z [INFO] Signature verification...
```

---

## Troubleshooting

### Issue: "No log streams found"

**Cause:** Lambda hasn't been invoked yet, so no logs exist.

**Solution:** Trigger the Lambda by:
1. Calling an API endpoint
2. Sending a test webhook from Meta
3. Using AWS Console to test the Lambda directly

### Issue: "Access Denied"

**Cause:** AWS credentials don't have CloudWatch Logs permissions.

**Solution:** Add this policy to your IAM user:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:605009361024:log-group:/aws/lambda/TrustGuard-*"
    }
  ]
}
```

---

## Quick Commands Cheat Sheet

```bash
# Webhook logs (most important for testing)
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1

# Auth logs (login, OTP)
aws logs tail /aws/lambda/TrustGuard-AuthService-dev --follow --region us-east-1

# All errors across all services
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1 --filter-pattern "ERROR"

# Last 50 log entries
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --region us-east-1 --since 10m
```

---

**Last Updated:** December 8, 2025  
**Region:** us-east-1  
**Stack:** TrustGuard-Dev
