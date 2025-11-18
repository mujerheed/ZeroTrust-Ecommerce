# Infrastructure Scripts

**Purpose**: Automation scripts for deployment, migration, and infrastructure management.

---

## 📁 Scripts Overview

### 1. `hybrid-migration.sh` - Infrastructure Migration

**Purpose**: Migrate from old SAM template to new template without data loss.

**What It Does**:
- ✅ Verifies existing DynamoDB tables (preserves all data)
- ✅ Creates new tables: `TrustGuard-Escalations`, `TrustGuard-CEOMapping`
- ✅ Adds `ByCEOID` GSI to `TrustGuard-Users` (multi-CEO tenancy)
- ✅ Enables Point-in-Time Recovery on critical tables
- ✅ Creates SNS topic for CEO escalation alerts
- ✅ Creates Secrets Manager secrets (JWT, Meta API)
- ✅ Generates environment configuration file

**Usage**:
```bash
# Run migration (safe, idempotent)
./hybrid-migration.sh

# Output will be written to:
# - CloudWatch Logs (for audit)
# - /tmp/trustguard-hybrid-config.env (environment variables)
```

**Prerequisites**:
- AWS CLI configured with valid credentials
- Permissions: `dynamodb:*`, `sns:*`, `secretsmanager:*`
- Existing tables: `TrustGuard-Users`, `TrustGuard-OTPs`, etc.

**Post-Migration Steps**:
1. Copy `/tmp/trustguard-hybrid-config.env` to `backend/.env`
2. Update Meta API credentials in Secrets Manager
3. Verify table names in `backend/common/config.py`

**Rollback**: Migration is additive (no deletions). To rollback:
```bash
# Delete new tables
aws dynamodb delete-table --table-name TrustGuard-Escalations
aws dynamodb delete-table --table-name TrustGuard-CEOMapping

# Delete SNS topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:{AccountId}:TrustGuard-EscalationAlert

# Delete secrets
aws secretsmanager delete-secret --secret-id /TrustGuard/dev/app --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id /TrustGuard/dev/meta --force-delete-without-recovery
```

---

### 2. `deploy.sh` - Deployment Automation

**Purpose**: Automated SAM build and deployment with validation.

**What It Does**:
- Validates AWS credentials
- Runs SAM build
- Validates CloudFormation template
- Deploys to specified environment (dev/prod)
- Outputs API Gateway URL

**Usage**:
```bash
# Deploy to dev environment (default)
./deploy.sh

# Deploy to production
./deploy.sh --environment prod

# Build only (no deploy)
./deploy.sh --build-only

# Skip tests (faster deployment)
./deploy.sh --skip-tests
```

**Options**:
- `--environment <env>`: Target environment (dev, prod)
- `--build-only`: Build SAM application without deploying
- `--skip-tests`: Skip pre-deployment validation tests
- `--help`: Show usage information

**Example Output**:
```
🚀 TrustGuard Deployment Script
================================

Environment: dev
Region: us-east-1

✅ Step 1: Validating AWS credentials...
✅ Step 2: Building SAM application...
✅ Step 3: Validating CloudFormation template...
✅ Step 4: Deploying to AWS...

🎉 Deployment Complete!
API Gateway URL: https://abc123.execute-api.us-east-1.amazonaws.com/Prod/
```

**Prerequisites**:
- AWS SAM CLI installed (`sam --version`)
- AWS CLI configured
- Docker running (for SAM local testing)

---

## 🧪 Testing Scripts

### Validate Infrastructure

```bash
#!/bin/bash
# Quick infrastructure validation

echo "Checking DynamoDB tables..."
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `TrustGuard`)]'

echo "Checking Lambda functions..."
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `trustguard`)].FunctionName'

echo "Checking SNS topics..."
aws sns list-topics --query 'Topics[?contains(TopicArn, `TrustGuard`)]'

echo "Checking S3 buckets..."
aws s3 ls | grep trustguard

echo "Checking Secrets Manager..."
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `TrustGuard`)].Name'
```

### Test Deployment

```bash
#!/bin/bash
# Test deployed API

API_URL=$(aws cloudformation describe-stacks \
  --stack-name trustguard-backend \
  --query 'Stacks[0].Outputs[?OutputKey==`WebAPIGatewayUrl`].OutputValue' \
  --output text)

echo "Testing API: $API_URL"

# Health check
curl -f "$API_URL/auth/health" || echo "❌ Health check failed"

echo "✅ API is responding"
```

---

## 🔧 Development Scripts

### Local Development Setup

```bash
#!/bin/bash
# setup-local-dev.sh

echo "Setting up local development environment..."

# Install Python dependencies
cd backend
pip3 install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env file (update with your values)"
fi

# Start local API
echo "Starting local API server..."
uvicorn app:app --reload --port 8000
```

### Database Seeding

```bash
#!/bin/bash
# seed-database.sh
# Populate tables with test data

echo "Seeding database with test data..."

# Create test CEO
aws dynamodb put-item \
  --table-name TrustGuard-Users \
  --item '{
    "user_id": {"S": "ceo_test_001"},
    "role": {"S": "CEO"},
    "name": {"S": "Test CEO"},
    "email": {"S": "ceo@example.com"},
    "phone": {"S": "+2348012345678"}
  }'

echo "✅ Test CEO created: ceo_test_001"

# Create test vendor
aws dynamodb put-item \
  --table-name TrustGuard-Users \
  --item '{
    "user_id": {"S": "vendor_test_001"},
    "role": {"S": "Vendor"},
    "ceo_id": {"S": "ceo_test_001"},
    "name": {"S": "Test Vendor"},
    "email": {"S": "vendor@example.com"}
  }'

echo "✅ Test vendor created: vendor_test_001"
```

---

## 📊 Monitoring Scripts

### View CloudWatch Logs

```bash
#!/bin/bash
# view-logs.sh <function-name>

FUNCTION_NAME=${1:-AuthServiceLambda}

LOG_GROUP=$(aws lambda get-function \
  --function-name "trustguard-backend-${FUNCTION_NAME}" \
  --query 'Configuration.LogGroupName' \
  --output text)

echo "Tailing logs for: $LOG_GROUP"
aws logs tail "$LOG_GROUP" --follow
```

### Monitor Lambda Metrics

```bash
#!/bin/bash
# monitor-metrics.sh

FUNCTIONS=("AuthServiceLambda" "VendorServiceLambda" "CEOServiceLambda")

for FUNC in "${FUNCTIONS[@]}"; do
  echo "📊 Metrics for $FUNC:"
  
  INVOCATIONS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value="trustguard-backend-${FUNC}" \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum \
    --query 'Datapoints[0].Sum' \
    --output text)
  
  echo "  Invocations (last hour): ${INVOCATIONS:-0}"
done
```

---

## 🔐 Security Scripts

### Rotate Secrets

```bash
#!/bin/bash
# rotate-jwt-secret.sh

echo "🔑 Rotating JWT secret..."

NEW_SECRET=$(openssl rand -base64 32 | tr -d '\n')

aws secretsmanager update-secret \
  --secret-id /TrustGuard/dev/app \
  --secret-string "{\"JWT_SECRET\":\"$NEW_SECRET\"}"

echo "✅ JWT secret rotated successfully"
echo "⚠️  All active sessions will be invalidated"
```

### Audit IAM Permissions

```bash
#!/bin/bash
# audit-iam.sh

echo "📋 Auditing IAM permissions..."

ROLES=$(aws iam list-roles \
  --query 'Roles[?contains(RoleName, `trustguard`)].RoleName' \
  --output text)

for ROLE in $ROLES; do
  echo "Role: $ROLE"
  aws iam list-attached-role-policies --role-name "$ROLE" --query 'AttachedPolicies[].PolicyArn'
done
```

---

## 🚀 CI/CD Integration

### GitHub Actions Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy TrustGuard

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy
        run: |
          cd infrastructure/scripts
          ./deploy.sh --environment prod --skip-tests
```

---

## 📚 Script Best Practices

### 1. **Always Check Exit Codes**
```bash
#!/bin/bash
set -e  # Exit on any error

aws dynamodb describe-table --table-name TrustGuard-Users
if [ $? -ne 0 ]; then
  echo "❌ Table not found"
  exit 1
fi
```

### 2. **Use Idempotent Operations**
```bash
# Check if resource exists before creating
if aws dynamodb describe-table --table-name TrustGuard-Escalations &>/dev/null; then
  echo "⚠️  Table already exists, skipping creation"
else
  aws dynamodb create-table ...
fi
```

### 3. **Log Everything**
```bash
LOG_FILE="/tmp/deployment-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "Deployment started at $(date)"
```

### 4. **Validate Prerequisites**
```bash
# Check AWS CLI
if ! command -v aws &> /dev/null; then
  echo "❌ AWS CLI not installed"
  exit 1
fi

# Check credentials
if ! aws sts get-caller-identity &> /dev/null; then
  echo "❌ AWS credentials not configured"
  exit 1
fi
```

---

## 🛠️ Troubleshooting

### Script Fails with "Permission Denied"
```bash
chmod +x infrastructure/scripts/*.sh
```

### AWS CLI Commands Timeout
```bash
# Increase timeout
aws configure set cli_read_timeout 30
```

### SAM Build Fails
```bash
# Clear cache and rebuild
rm -rf .aws-sam
sam build --use-container
```

---

**Last Updated**: 19 November 2025  
**Maintainer**: Senior Cloud Architect
