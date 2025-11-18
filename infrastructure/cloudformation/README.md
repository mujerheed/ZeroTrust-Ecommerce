# CloudFormation Templates

**Purpose**: AWS SAM (Serverless Application Model) templates for TrustGuard infrastructure.

---

## 📁 Files Overview

### Active Templates

#### `trustguard-template.yaml` ✅ **CURRENT**
**Latest SAM template** with all infrastructure components for TrustGuard.

**Includes**:
- 7 DynamoDB tables (Users, OTPs, Orders, Receipts, AuditLogs, Escalations, CEOMapping)
- S3 bucket for encrypted receipt storage
- SNS topic for CEO escalation alerts
- Secrets Manager secrets (JWT, Meta API)
- 4 Lambda functions (Auth, Vendor, CEO, Receipt services)
- IAM roles with least-privilege policies
- Global Secondary Indexes for multi-CEO tenancy

**Key Features**:
- Pay-per-request billing (no capacity planning)
- Point-in-Time Recovery on critical tables
- Server-side encryption (SSE-S3/KMS)
- Auto-scaling (serverless)

---

### Archive/Backup Templates

#### `trustguard-template-old.yaml` 🗄️ **ARCHIVED**
**Previous version** before hybrid migration (November 2025).

**What Changed**:
- Missing: Escalations and CEOMapping tables
- Missing: SNS topic for CEO alerts
- Missing: Secrets Manager integration
- Missing: Multi-CEO tenancy GSIs
- Missing: PITR on tables

**Keep for**: Rollback reference, infrastructure audit trail.

---

### Documentation

#### `TEMPLATE_COMPARISON.md` (moved to `docs/`)
**Comprehensive comparison** between old and new templates.

**Covers**:
- Breaking changes (table names, encryption, GSIs)
- Migration strategy (hybrid approach)
- Rollback procedures
- Infrastructure validation commands

**View at**: `../../docs/TEMPLATE_COMPARISON.md`

---

## 🏗️ Template Structure

### Parameters
```yaml
Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, prod]
  
  HighValueThreshold:
    Type: Number
    Default: 1000000  # ₦1,000,000
  
  BucketNamePrefix:
    Type: String
    Default: trustguard-receipts
```

### Globals
```yaml
Globals:
  Function:
    Runtime: python3.11
    MemorySize: 256
    Timeout: 15
    Handler: app.lambda_handler
```

### Resources
- **DynamoDB Tables** (7): User data, orders, escalations
- **S3 Bucket** (1): Encrypted receipt storage
- **SNS Topics** (1): CEO alerts
- **Secrets Manager** (2): JWT secret, Meta API credentials
- **Lambda Functions** (4): Auth, Vendor, CEO, Receipt services
- **IAM Roles** (4): Per-Lambda least-privilege policies

---

## 🚀 Deployment

### Using SAM CLI

```bash
# Build application
sam build

# Deploy (first time)
sam deploy --guided

# Deploy (subsequent)
sam deploy

# Deploy to production
sam deploy --config-env prod
```

### Using AWS Console

1. **Upload Template**:
   - Go to CloudFormation console
   - Click "Create Stack"
   - Upload `trustguard-template.yaml`

2. **Configure Parameters**:
   - Environment: `dev` or `prod`
   - HighValueThreshold: `1000000` (₦1M)
   - BucketNamePrefix: `trustguard-receipts`

3. **Review and Create**:
   - Acknowledge IAM role creation
   - Create stack

---

## 🔧 Customization

### Change Lambda Memory/Timeout

```yaml
Globals:
  Function:
    MemorySize: 512  # Increase from 256 MB
    Timeout: 30      # Increase from 15 seconds
```

### Add New Table

```yaml
TrustGuardNewTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub "TrustGuard-NewTable-${Environment}"
    AttributeDefinitions:
      - AttributeName: id
        AttributeType: S
    KeySchema:
      - AttributeName: id
        KeyType: HASH
    BillingMode: PAY_PER_REQUEST
    SSESpecification:
      SSEEnabled: true
```

### Add Environment Variable to Lambda

```yaml
AuthServiceLambda:
  Type: AWS::Serverless::Function
  Properties:
    Environment:
      Variables:
        NEW_VAR: !Ref NewParameter
```

---

## 📊 Resource Limits

### DynamoDB
- **Tables**: 7 (within 2500 table limit per region)
- **GSIs**: 12 total (5 per table limit)
- **Billing**: Pay-per-request (no provisioned capacity)

### Lambda
- **Functions**: 4 (within 1000 function limit)
- **Concurrent executions**: Auto-scales (up to account limit)
- **Memory**: 256 MB (configurable 128 MB - 10,240 MB)

### S3
- **Buckets**: 1 (within 100 bucket limit per account)
- **Objects**: Unlimited
- **Storage**: Unlimited (pay per GB)

---

## 🔐 Security Features

### Encryption at Rest
- **DynamoDB**: SSE with AWS-managed keys
- **S3**: SSE-S3 (AES256)
- **Secrets Manager**: Encrypted with AWS-managed keys

### Encryption in Transit
- **API Gateway**: HTTPS only
- **DynamoDB**: TLS 1.2+
- **S3**: SSL/TLS required (bucket policy enforced)

### IAM Least Privilege
Each Lambda has minimal permissions:
```yaml
VendorServiceLambda:
  Policies:
    - DynamoDBCrudPolicy:
        TableName: !Ref TrustGuardOrdersTable  # Only Orders table
    - S3ReadPolicy:
        BucketName: !Ref TrustGuardReceiptBucket  # Read-only
```

---

## 🧪 Validation

### Validate Template Syntax

```bash
# Using SAM
sam validate

# Using AWS CLI
aws cloudformation validate-template \
  --template-body file://trustguard-template.yaml
```

### Estimate Costs

```bash
# Generate cost estimate
sam deploy --guided --dry-run

# View pricing in CloudFormation console
# (during stack creation preview)
```

---

## 🛠️ Troubleshooting

### Stack Creation Fails

**Error**: `Resource creation failed: TrustGuard-Users already exists`
```bash
# Solution: Use different table names or delete existing table
aws dynamodb delete-table --table-name TrustGuard-Users
```

**Error**: `Insufficient permissions to create IAM role`
```bash
# Solution: Add CAPABILITY_IAM
sam deploy --capabilities CAPABILITY_IAM
```

### Stack Update Fails

**Error**: `No updates are to be performed`
```bash
# Solution: This is not an error, stack is already up-to-date
```

**Error**: `Resource cannot be updated (immutable property)`
```bash
# Solution: Delete and recreate resource, or create new stack
```

### Rollback Stack

```bash
# Rollback to previous version
aws cloudformation cancel-update-stack --stack-name trustguard-backend

# Delete failed stack
aws cloudformation delete-stack --stack-name trustguard-backend
```

---

## 📋 Build Output

The `build/` directory contains SAM build artifacts:

```
build/
├── template.yaml                    # Processed SAM template
├── samconfig.toml                   # Build configuration
├── AuthServiceLambda/               # Built Lambda package
│   ├── app.py
│   ├── auth_service/
│   ├── common/
│   ├── vendor_service/
│   ├── ceo_service/
│   └── dependencies (boto3, fastapi, etc.)
├── VendorServiceLambda/             # Built Lambda package
├── CEOServiceLambda/                # Built Lambda package
└── ReceiptServiceLambda/            # Built Lambda package
```

**Note**: `build/` is in `.gitignore` (not committed to version control).

---

## 🔄 Version History

| Version | Date | Changes | Migration Required |
|---------|------|---------|-------------------|
| 2.0 | 2025-11-19 | Added Escalations, CEOMapping, SNS, Secrets Manager, PITR | ✅ Yes (hybrid) |
| 1.0 | 2025-10-07 | Initial SAM template with 5 tables, S3, Lambdas | N/A |

---

## 📚 Related Documentation

- [Template Comparison Guide](../../docs/TEMPLATE_COMPARISON.md) - Old vs New diff
- [Infrastructure README](../README.md) - Deployment guide
- [Hybrid Migration Script](../scripts/hybrid-migration.sh) - Migration automation
- [Implementation Summary](../../docs/IMPLEMENTATION_SUMMARY.md) - Complete setup guide

---

**Last Updated**: 19 November 2025  
**Template Version**: 2.0  
**Maintainer**: Senior Cloud Architect
