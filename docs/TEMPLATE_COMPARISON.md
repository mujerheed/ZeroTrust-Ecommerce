# SAM Template Comparison: Old vs New

**Date**: 19 November 2025  
**Purpose**: Identify critical differences between existing AWS resources and new template requirements

---

## 🚨 CRITICAL COMPATIBILITY ISSUE

**Your existing AWS tables are NOT compatible with the new template.** You have 3 options:

### Option 1: **RECOMMENDED - Use Hybrid Approach** ⭐
Keep your existing tables, manually create missing resources, update config.py to use existing table names.

### Option 2: **Create Parallel Environment**
Deploy new template to dev account/region, migrate data later.

### Option 3: **Destructive Migration** ⚠️
Delete existing tables, deploy new template (data loss unless backed up).

---

## 📊 Key Differences Summary

| Component | Old Template | New Template | Impact |
|-----------|--------------|--------------|--------|
| **Table Names** | `TrustGuard-Users` | `TrustGuard-Users-{Environment}` | ❌ **BREAKING** |
| **KMS Encryption** | Default AWS-managed | Customer-managed key | ❌ **BREAKING** |
| **Missing Tables** | None | Escalations, CEOMapping | ❌ **BLOCKING** |
| **Secrets Manager** | Hardcoded JWT | Secrets Manager integration | ⚠️ **Required** |
| **Runtime** | Python 3.11 | Python 3.12 | ⚠️ Compatible |
| **GSI Indexes** | Limited | Enhanced multi-tenancy | ⚠️ **Schema change** |

---

## 🔍 Detailed Component Analysis

### 1️⃣ DynamoDB Tables

#### **TrustGuardUsersTable**
**Old:**
```yaml
TableName: TrustGuard-Users
AttributeDefinitions:
  - user_id (S)
KeySchema:
  - user_id (HASH)
SSESpecification:
  SSEEnabled: true  # AWS-managed key
```

**New:**
```yaml
TableName: TrustGuard-Users-{Environment}  # ❌ BREAKING
AttributeDefinitions:
  - user_id (S)
  - ceo_id (S)  # ⚠️ NEW
KeySchema:
  - user_id (HASH)
GlobalSecondaryIndexes:
  - ByCEOID (ceo_id HASH)  # ⚠️ NEW - Multi-CEO tenancy
SSESpecification:
  SSEType: KMS  # ❌ BREAKING - Requires customer-managed key
  KMSMasterKeyId: !Ref TrustGuardKMSKey
PointInTimeRecoverySpecification:
  PointInTimeRecoveryEnabled: true  # ✅ NEW - Data protection
```

**Impact**: 
- Table name mismatch prevents stack update
- New GSI `ByCEOID` requires adding `ceo_id` attribute to ALL existing user records
- Switching to KMS encryption requires table recreation (can't modify in-place)

---

#### **TrustGuardOTPsTable**
**Old:**
```yaml
TableName: TrustGuard-OTPs
KeySchema:
  - user_id (HASH)
```

**New:**
```yaml
TableName: TrustGuard-OTPs-{Environment}  # ❌ BREAKING
KeySchema:
  - user_id (HASH)
  - request_id (RANGE)  # ⚠️ NEW - Multiple concurrent OTPs
SSEType: KMS  # ❌ BREAKING
```

**Impact**:
- Composite key change (adding `request_id` as RANGE key) requires table recreation
- Current OTPs will be incompatible

---

#### **TrustGuardOrdersTable**
**Old:**
```yaml
TableName: TrustGuard-Orders
GlobalSecondaryIndexes:
  - VendorIndex (vendor_id HASH, created_at RANGE)
  - VendorStatusIndex (vendor_id HASH, order_status RANGE)
  - BuyerIndex (buyer_id HASH, created_at RANGE)
```

**New:**
```yaml
TableName: TrustGuard-Orders-{Environment}  # ❌ BREAKING
AttributeDefinitions:
  - ceo_id (S)  # ⚠️ NEW
GlobalSecondaryIndexes:
  - ByVendorAndCEO (vendor_id HASH, ceo_id RANGE)  # ⚠️ DIFFERENT
```

**Impact**:
- Lost GSIs: `VendorStatusIndex`, `BuyerIndex` (your existing code may rely on these!)
- New multi-CEO isolation requires `ceo_id` on all orders

---

#### **TrustGuardReceiptsTable**
**Old:**
```yaml
TableName: TrustGuard-Receipts
KeySchema:
  - order_id (HASH)
GlobalSecondaryIndexes:
  - UploadTimeIndex (uploaded_at HASH)  # ⚠️ Wrong key type
```

**New:**
```yaml
# ❌ MISSING from new template!
```

**Impact**: New template doesn't define a Receipts table! This is a regression.

---

### 2️⃣ NEW Tables (Not in Old Template)

#### **TrustGuardEscalationsTable** ✅ REQUIRED
```yaml
TableName: TrustGuard-Escalations-{Environment}
KeySchema:
  - escalation_id (HASH)
GlobalSecondaryIndexes:
  - ByCEOPending (ceo_id HASH, status RANGE)
```
**Purpose**: CEO approval workflow for high-value transactions (≥₦1M)

#### **TrustGuardCEOMappingTable** ✅ REQUIRED
```yaml
TableName: TrustGuard-CEOMapping-{Environment}
KeySchema:
  - phone_number_id (HASH)
GlobalSecondaryIndexes:
  - ByPageID (page_id HASH)
```
**Purpose**: Multi-CEO webhook routing (WhatsApp/Instagram → ceo_id mapping)

---

### 3️⃣ KMS Key (NEW)

**Old**: Not present (uses AWS-managed encryption)

**New**:
```yaml
TrustGuardKMSKey:
  Type: AWS::KMS::Key
  Properties:
    EnableKeyRotation: true
    PendingWindowInDays: 7
```

**Impact**: 
- All DynamoDB tables now require KMS encryption
- S3 bucket encryption changes from SSE-S3 (`AES256`) to SSE-KMS
- Cannot modify existing encrypted resources to use different key

---

### 4️⃣ Secrets Manager (NEW)

**Old**: Hardcoded in Globals
```yaml
Environment:
  Variables:
    JWT_SECRET: "temporary-dev-secret-key-change-later"  # ⚠️ INSECURE
```

**New**:
```yaml
TrustGuardSecrets:
  Type: AWS::SecretsManager::Secret
  Name: /TrustGuard/{Environment}/app
  KmsKeyId: !Ref TrustGuardKMSKey

TrustGuardMetaSecrets:
  Type: AWS::SecretsManager::Secret
  Name: /TrustGuard/{Environment}/meta
```

**Impact**: 
- `config.py` now calls `get_jwt_secret()` from Secrets Manager
- Requires one-time secret creation/migration

---

### 5️⃣ S3 Bucket

**Old:**
```yaml
BucketName: trustguard-receipts-{AccountId}-{Region}
BucketEncryption:
  SSEAlgorithm: AES256  # AWS-managed
```

**New:**
```yaml
BucketName: trustguard-receipts-{AccountId}-{Environment}  # ⚠️ Name change
BucketEncryption:
  SSEAlgorithm: aws:kms  # ❌ BREAKING
  KMSMasterKeyID: !Ref TrustGuardKMSKey
VersioningConfiguration:
  Status: Enabled  # ✅ NEW - Immutability
PublicAccessBlockConfiguration: # ✅ NEW - Security
```

**New Bucket Policies:**
```yaml
- DenyUnencryptedObjectUploads (requires KMS)
- DenyInsecureTransport (requires HTTPS)
```

**Impact**:
- Bucket name change breaks existing S3 presigned URLs
- Existing objects encrypted with SSE-S3, new objects require SSE-KMS
- Bucket policies will deny uploads from old code not specifying KMS

---

### 6️⃣ SNS Topic (NEW)

**Old**: Not present

**New**:
```yaml
EscalationAlertTopic:
  Type: AWS::SNS::Topic
  TopicName: TrustGuard-EscalationAlert-{Environment}
  KmsMasterKeyId: !Ref TrustGuardKMSKey
```

**Purpose**: CEO notifications for high-value escalations

---

### 7️⃣ Lambda Functions

| Property | Old | New | Impact |
|----------|-----|-----|--------|
| **Runtime** | python3.11 | python3.12 | ⚠️ Compatible, minor |
| **Memory** | 256 MB | 512 MB | ✅ Better performance |
| **Timeout** | 15s | 30s | ✅ More headroom |
| **IAM Role** | Inline policies | Centralized `LambdaExecutionRole` | ⚠️ Architecture change |

---

## 🛠️ RECOMMENDED MIGRATION PATH

### **Hybrid Approach** (Minimal Disruption)

#### Step 1: Inventory Your Existing Resources
```bash
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `TrustGuard`)]'
aws s3 ls | grep trustguard
aws secretsmanager list-secrets --query 'SecretList[?contains(Name, `TrustGuard`)]'
```

#### Step 2: Manually Create Missing Resources
```bash
# Create Escalations table (keep existing naming convention)
aws dynamodb create-table \
  --table-name TrustGuard-Escalations \
  --attribute-definitions \
      AttributeName=escalation_id,AttributeType=S \
      AttributeName=ceo_id,AttributeType=S \
      AttributeName=status,AttributeType=S \
  --key-schema AttributeName=escalation_id,KeyType=HASH \
  --global-secondary-indexes \
      "IndexName=ByCEOPending,KeySchema=[{AttributeName=ceo_id,KeyType=HASH},{AttributeName=status,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
  --billing-mode PAY_PER_REQUEST \
  --sse-specification Enabled=true

# Create CEOMapping table
aws dynamodb create-table \
  --table-name TrustGuard-CEOMapping \
  --attribute-definitions \
      AttributeName=phone_number_id,AttributeType=S \
      AttributeName=page_id,AttributeType=S \
  --key-schema AttributeName=phone_number_id,KeyType=HASH \
  --global-secondary-indexes \
      "IndexName=ByPageID,KeySchema=[{AttributeName=page_id,KeyType=HASH}],Projection={ProjectionType=ALL}" \
  --billing-mode PAY_PER_REQUEST \
  --sse-specification Enabled=true

# Create SNS topic
aws sns create-topic --name TrustGuard-EscalationAlert

# Create Secrets Manager secrets
aws secretsmanager create-secret \
  --name /TrustGuard/dev/app \
  --secret-string '{"JWT_SECRET":"your-secure-random-key-here"}'

aws secretsmanager create-secret \
  --name /TrustGuard/dev/meta \
  --secret-string '{"APP_ID":"your-meta-app-id","APP_SECRET":"your-meta-app-secret"}'
```

#### Step 3: Update `backend/common/config.py`
```python
class Settings(BaseSettings):
    # Use existing table names (no -dev suffix)
    USERS_TABLE: str = "TrustGuard-Users"
    OTPS_TABLE: str = "TrustGuard-OTPs"
    AUDIT_LOGS_TABLE: str = "TrustGuard-AuditLogs"
    ORDERS_TABLE: str = "TrustGuard-Orders"
    RECEIPTS_TABLE: str = "TrustGuard-Receipts"  # Keep using old table
    
    # New tables (manually created)
    ESCALATIONS_TABLE: str = "TrustGuard-Escalations"
    CEO_MAPPING_TABLE: str = "TrustGuard-CEOMapping"
    
    # SNS topic ARN (get from AWS console)
    ESCALATION_SNS_TOPIC_ARN: str = "arn:aws:sns:us-east-1:123456789012:TrustGuard-EscalationAlert"
    
    # Existing S3 bucket
    RECEIPT_BUCKET: str = "trustguard-receipts-123456789012-us-east-1"
    
    HIGH_VALUE_THRESHOLD: int = 1000000
    ENVIRONMENT: str = "dev"
```

#### Step 4: Add Missing GSI to Existing Users Table
```bash
# Add ByCEOID GSI to existing Users table
aws dynamodb update-table \
  --table-name TrustGuard-Users \
  --attribute-definitions AttributeName=ceo_id,AttributeType=S \
  --global-secondary-index-updates \
    "[{\"Create\":{\"IndexName\":\"ByCEOID\",\"KeySchema\":[{\"AttributeName\":\"ceo_id\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}}]"
```

#### Step 5: Enable Point-in-Time Recovery (PITR)
```bash
aws dynamodb update-continuous-backups \
  --table-name TrustGuard-Users \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name TrustGuard-Orders \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name TrustGuard-Escalations \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

#### Step 6: Test Escalation Workflow
```bash
# Verify new tables and indexes work
python -m pytest backend/ceo_service/tests/test_approval.py -v
```

---

## ⚠️ What You CANNOT Do Without Data Loss

1. **Rename existing tables** (DynamoDB doesn't support table rename)
2. **Change primary key schema** (requires table recreation)
3. **Switch encryption keys** on existing tables (requires recreation)
4. **Modify S3 bucket name** (requires new bucket, data migration)

---

## ✅ What You CAN Do Safely

1. **Add GSIs** to existing tables (non-blocking, backfilled automatically)
2. **Enable PITR** on existing tables (no data impact)
3. **Create new tables** alongside existing ones
4. **Create Secrets Manager secrets** (doesn't affect existing resources)
5. **Update Lambda function code** (deploy new versions)

---

## 🎯 Decision Matrix

| Your Situation | Recommended Action |
|----------------|-------------------|
| **Production data exists** | ✅ Hybrid Approach (Steps 1-6 above) |
| **Only test data** | ✅ Delete all, deploy new template fresh |
| **Multiple AWS accounts** | ✅ Deploy new template to dev account, migrate prod later |
| **Need to preserve S3 objects** | ⚠️ Hybrid + manual S3 copy (bucket name changed) |

---

## 📋 Action Items for You

**Before proceeding with escalation workflow implementation:**

1. ✅ **Verify existing table names:**
   ```bash
   aws dynamodb describe-table --table-name TrustGuard-Users --query 'Table.TableName'
   aws dynamodb describe-table --table-name TrustGuard-Orders --query 'Table.TableName'
   ```

2. ✅ **Check if Escalations table exists:**
   ```bash
   aws dynamodb describe-table --table-name TrustGuard-Escalations 2>&1
   ```

3. ✅ **Decide on migration approach:**
   - [ ] Hybrid (use existing tables + create missing resources)
   - [ ] Fresh deployment (delete all, start clean)
   - [ ] Parallel environment (new AWS account/region)

4. ✅ **Update config.py** to match your chosen approach

5. ✅ **Run infrastructure validation:**
   ```bash
   python backend/scripts/validate_infrastructure.py
   ```

---

**Senior Architect, which migration approach do you want to use?** I'll update the config.py and implementation accordingly.
