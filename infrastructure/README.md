# Infrastructure

**Purpose**: AWS infrastructure as code (SAM templates), deployment scripts, and CloudFormation resources.

---

## 📁 Directory Structure

```
infrastructure/
├── cloudformation/          # SAM/CloudFormation templates
│   ├── trustguard-template.yaml        # Main SAM template (active)
│   ├── trustguard-template-old.yaml    # Backup (pre-migration)
│   ├── TEMPLATE_COMPARISON.md          # Migration guide
│   └── build/                          # SAM build output
├── scripts/
│   ├── deploy.sh                       # Deployment automation
│   └── hybrid-migration.sh             # Infrastructure migration script
└── samconfig.toml                      # SAM CLI configuration
```

---

## 🏗️ SAM Template Overview

### Current Template: `trustguard-template.yaml`

**Infrastructure Components**:

#### 1. **DynamoDB Tables** (7 total)
- `TrustGuard-Users` - User accounts (Buyers, Vendors, CEOs)
- `TrustGuard-OTPs` - Time-limited OTP codes (TTL enabled)
- `TrustGuard-Orders` - Transaction records
- `TrustGuard-Receipts` - Receipt metadata
- `TrustGuard-AuditLogs` - Immutable security logs
- `TrustGuard-Escalations` - CEO approval workflow (≥₦1M transactions)
- `TrustGuard-CEOMapping` - WhatsApp/Instagram → CEO routing

**Key Features**:
- ✅ Pay-per-request billing (no capacity planning)
- ✅ Point-in-Time Recovery (PITR) on critical tables
- ✅ AWS-managed encryption at rest
- ✅ Global Secondary Indexes (GSI) for multi-CEO tenancy

#### 2. **S3 Bucket**
- `trustguard-receipts-{AccountId}-{Region}`
- Server-side encryption: SSE-S3 (AES256)
- Versioning enabled
- Public access blocked
- Lifecycle rules for incomplete multipart uploads

#### 3. **SNS Topics**
- `TrustGuard-EscalationAlert` - CEO notifications (SMS + Email)

#### 4. **Secrets Manager**
- `/TrustGuard/dev/app` - JWT signing key
- `/TrustGuard/dev/meta` - Meta API credentials (per CEO)

#### 5. **Lambda Functions** (4)
- `AuthServiceLambda` - OTP generation/verification
- `VendorServiceLambda` - Order management, receipt verification
- `CEOServiceLambda` - Escalation approvals, vendor management
- `ReceiptServiceLambda` - S3 presigned URLs, receipt uploads

**Runtime**: Python 3.11  
**Memory**: 256 MB  
**Timeout**: 15 seconds  
**Handler**: `app.lambda_handler` (via Mangum adapter)

---

## 🚀 Deployment

### Prerequisites

```bash
# Install AWS SAM CLI
brew install aws-sam-cli  # macOS
# or
pip install aws-sam-cli

# Configure AWS credentials
aws configure
```

### Local Testing

```bash
# Build the application
cd infrastructure/cloudformation
sam build

# Start local API Gateway
sam local start-api --port 8000

# Test endpoint
curl http://localhost:8000/auth/health
```

### Deploy to AWS

```bash
# First-time deployment (guided)
sam deploy --guided

# Subsequent deployments
sam deploy

# Deploy to specific environment
sam deploy --config-env prod
```

### Using Deployment Script

```bash
# Automated deployment with validation
cd infrastructure/scripts
./deploy.sh

# Options:
./deploy.sh --environment dev     # Deploy to dev
./deploy.sh --environment prod    # Deploy to prod
./deploy.sh --build-only          # Build without deploying
```

---

## 🔧 Hybrid Migration

**Purpose**: Migrate from old template to new template without data loss.

### What Was Migrated

✅ **Preserved Existing Resources**:
- All 5 original DynamoDB tables
- S3 bucket with existing receipts
- No data loss

✅ **Created New Resources**:
- `TrustGuard-Escalations` table
- `TrustGuard-CEOMapping` table
- SNS topic for CEO alerts
- Secrets Manager secrets
- Point-in-Time Recovery on critical tables

### Running Migration

```bash
cd infrastructure/scripts
./hybrid-migration.sh
```

**Output**:
```
✅ TrustGuard-Escalations created
✅ TrustGuard-CEOMapping created
✅ SNS Topic: arn:aws:sns:us-east-1:605009361024:TrustGuard-EscalationAlert
✅ Secrets Manager: /TrustGuard/dev/app
✅ Secrets Manager: /TrustGuard/dev/meta
✅ PITR enabled on critical tables
```

**Post-Migration**:
1. Update Meta API credentials in Secrets Manager
2. Copy `/tmp/trustguard-hybrid-config.env` to `backend/.env`
3. Verify table names in `backend/common/config.py`

---

## 📋 SAM Configuration

### File: `samconfig.toml`

```toml
version = 0.1

[default]
[default.deploy]
[default.deploy.parameters]
stack_name = "trustguard-backend"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket"
s3_prefix = "trustguard-backend"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
confirm_changeset = true
```

**Parameters**:
- `stack_name`: CloudFormation stack name
- `s3_bucket`: SAM artifacts bucket (auto-created)
- `region`: AWS region for deployment
- `capabilities`: IAM role creation permission

---

## 🔐 Security Best Practices

### 1. **Least Privilege IAM Policies**

Each Lambda has scoped permissions:

```yaml
VendorServiceLambda:
  Policies:
    - DynamoDBCrudPolicy:
        TableName: !Ref TrustGuardOrdersTable
    - Statement:
        Effect: Allow
        Action: dynamodb:Query
        Resource: !Sub "${TrustGuardOrdersTable.Arn}/index/VendorIndex"
```

### 2. **Encryption at Rest**

```yaml
SSESpecification:
  SSEEnabled: true
  # Uses AWS-managed keys (default)
```

### 3. **Secrets Management**

```yaml
# ❌ NEVER hardcode secrets in template
Environment:
  Variables:
    JWT_SECRET: "hardcoded-secret"  # BAD!

# ✅ Use Secrets Manager
Environment:
  Variables:
    SECRETS_PATH_APP: /TrustGuard/dev/app
```

### 4. **S3 Bucket Security**

```yaml
PublicAccessBlockConfiguration:
  BlockPublicAcls: true
  BlockPublicPolicy: true
  IgnorePublicAcls: true
  RestrictPublicBuckets: true
```

---

## 🧪 Validation

### Verify Infrastructure

```bash
# List all TrustGuard tables
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `TrustGuard`)]'

# Check Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `trustguard`)].FunctionName'

# Verify SNS topic
aws sns list-topics --query 'Topics[?contains(TopicArn, `TrustGuard`)]'

# Check S3 bucket
aws s3 ls | grep trustguard

# Verify Secrets Manager
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `TrustGuard`)].Name'
```

### Test Deployment

```bash
# Get API Gateway URL
aws cloudformation describe-stacks \
  --stack-name trustguard-backend \
  --query 'Stacks[0].Outputs[?OutputKey==`WebAPIGatewayUrl`].OutputValue' \
  --output text

# Test health endpoint
curl https://{api-id}.execute-api.us-east-1.amazonaws.com/Prod/auth/health
```

---

## 📊 Monitoring & Logs

### CloudWatch Logs

Each Lambda function creates log groups:
```
/aws/lambda/trustguard-backend-AuthServiceLambda-ABC123
/aws/lambda/trustguard-backend-VendorServiceLambda-DEF456
/aws/lambda/trustguard-backend-CEOServiceLambda-GHI789
```

**View logs**:
```bash
# Stream logs in real-time
sam logs --name AuthServiceLambda --tail

# Get recent logs
aws logs tail /aws/lambda/trustguard-backend-AuthServiceLambda-ABC123 --follow
```

### CloudWatch Metrics

- Lambda invocations
- DynamoDB consumed capacity
- S3 request metrics
- SNS delivery success rate

**View metrics**:
```bash
# Lambda invocations (last 1 hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=trustguard-backend-AuthServiceLambda-ABC123 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. SAM Build Fails**
```bash
# Error: "Error: PythonPipBuilder:ResolveDependencies"
# Solution: Ensure Python 3.11 is installed
python3 --version
pip3 install -r backend/requirements.txt
```

**2. Deployment Fails - IAM Permissions**
```bash
# Error: "User is not authorized to perform: iam:CreateRole"
# Solution: Add CAPABILITY_IAM to deploy command
sam deploy --capabilities CAPABILITY_IAM
```

**3. Lambda Timeout**
```bash
# Error: "Task timed out after 15.00 seconds"
# Solution: Increase timeout in template
Timeout: 30  # Increase from 15 to 30 seconds
```

**4. DynamoDB Throttling**
```bash
# Error: "ProvisionedThroughputExceededException"
# Solution: Already using PAY_PER_REQUEST mode (no action needed)
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aws-actions/setup-sam@v2
      - uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: SAM Build
        run: sam build
      
      - name: SAM Deploy
        run: sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
```

---

## 📚 Additional Resources

- [SAM Template Comparison](./cloudformation/TEMPLATE_COMPARISON.md) - Old vs New template diff
- [Hybrid Migration Script](./scripts/hybrid-migration.sh) - Infrastructure migration automation
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)

---

**Last Updated**: 19 November 2025  
**Maintainer**: Senior Cloud Architect
