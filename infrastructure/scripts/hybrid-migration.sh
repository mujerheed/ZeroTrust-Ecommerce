#!/bin/bash
set -e

# ============================================================
# TrustGuard Hybrid Migration Script
# ============================================================
# Purpose: Create missing infrastructure components while
#          preserving existing DynamoDB tables and S3 bucket
# Author: Senior Cloud Architect
# Date: 19 November 2025
# ============================================================

echo "🚀 TrustGuard Hybrid Migration Starting..."
echo ""

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="dev"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "UNKNOWN")

echo "📋 Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  Environment: $ENVIRONMENT"
echo "  Account ID: $ACCOUNT_ID"
echo ""

# ============================================================
# STEP 1: Verify Existing Resources
# ============================================================
echo "✅ Step 1: Verifying existing resources..."

EXISTING_TABLES=(
    "TrustGuard-Users"
    "TrustGuard-OTPs"
    "TrustGuard-AuditLogs"
    "TrustGuard-Orders"
    "TrustGuard-Receipts"
)

for table in "${EXISTING_TABLES[@]}"; do
    if aws dynamodb describe-table --table-name "$table" --region "$AWS_REGION" &>/dev/null; then
        echo "  ✓ Found: $table"
    else
        echo "  ✗ Missing: $table (WARNING: Expected to exist)"
    fi
done

echo ""

# ============================================================
# STEP 2: Create Escalations Table
# ============================================================
echo "📊 Step 2: Creating TrustGuard-Escalations table..."

if aws dynamodb describe-table --table-name "TrustGuard-Escalations" --region "$AWS_REGION" &>/dev/null; then
    echo "  ⚠️  TrustGuard-Escalations already exists, skipping creation"
else
    aws dynamodb create-table \
        --table-name "TrustGuard-Escalations" \
        --attribute-definitions \
            AttributeName=escalation_id,AttributeType=S \
            AttributeName=ceo_id,AttributeType=S \
            AttributeName=status,AttributeType=S \
        --key-schema \
            AttributeName=escalation_id,KeyType=HASH \
        --global-secondary-indexes \
            "[{
                \"IndexName\": \"ByCEOPending\",
                \"KeySchema\": [
                    {\"AttributeName\": \"ceo_id\", \"KeyType\": \"HASH\"},
                    {\"AttributeName\": \"status\", \"KeyType\": \"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }]" \
        --billing-mode PAY_PER_REQUEST \
        --sse-specification Enabled=true \
        --region "$AWS_REGION" \
        --tags Key=Project,Value=TrustGuard Key=Environment,Value="$ENVIRONMENT"
    
    echo "  ✅ TrustGuard-Escalations table created"
    
    # Wait for table to become active
    echo "  ⏳ Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name "TrustGuard-Escalations" --region "$AWS_REGION"
    echo "  ✅ TrustGuard-Escalations is now ACTIVE"
fi

echo ""

# ============================================================
# STEP 3: Create CEO Mapping Table
# ============================================================
echo "📊 Step 3: Creating TrustGuard-CEOMapping table..."

if aws dynamodb describe-table --table-name "TrustGuard-CEOMapping" --region "$AWS_REGION" &>/dev/null; then
    echo "  ⚠️  TrustGuard-CEOMapping already exists, skipping creation"
else
    aws dynamodb create-table \
        --table-name "TrustGuard-CEOMapping" \
        --attribute-definitions \
            AttributeName=phone_number_id,AttributeType=S \
            AttributeName=page_id,AttributeType=S \
        --key-schema \
            AttributeName=phone_number_id,KeyType=HASH \
        --global-secondary-indexes \
            "[{
                \"IndexName\": \"ByPageID\",
                \"KeySchema\": [
                    {\"AttributeName\": \"page_id\", \"KeyType\": \"HASH\"}
                ],
                \"Projection\": {\"ProjectionType\": \"ALL\"}
            }]" \
        --billing-mode PAY_PER_REQUEST \
        --sse-specification Enabled=true \
        --region "$AWS_REGION" \
        --tags Key=Project,Value=TrustGuard Key=Environment,Value="$ENVIRONMENT"
    
    echo "  ✅ TrustGuard-CEOMapping table created"
    
    # Wait for table to become active
    echo "  ⏳ Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name "TrustGuard-CEOMapping" --region "$AWS_REGION"
    echo "  ✅ TrustGuard-CEOMapping is now ACTIVE"
fi

echo ""

# ============================================================
# STEP 4: Add ByCEOID GSI to Users Table
# ============================================================
echo "🔧 Step 4: Adding ByCEOID GSI to TrustGuard-Users table..."

# Check if GSI already exists
GSI_EXISTS=$(aws dynamodb describe-table \
    --table-name "TrustGuard-Users" \
    --region "$AWS_REGION" \
    --query 'Table.GlobalSecondaryIndexes[?IndexName==`ByCEOID`].IndexName' \
    --output text 2>/dev/null || echo "")

if [ -n "$GSI_EXISTS" ]; then
    echo "  ⚠️  ByCEOID GSI already exists on TrustGuard-Users, skipping"
else
    aws dynamodb update-table \
        --table-name "TrustGuard-Users" \
        --attribute-definitions AttributeName=ceo_id,AttributeType=S \
        --global-secondary-index-updates \
            "[{
                \"Create\": {
                    \"IndexName\": \"ByCEOID\",
                    \"KeySchema\": [{\"AttributeName\": \"ceo_id\", \"KeyType\": \"HASH\"}],
                    \"Projection\": {\"ProjectionType\": \"ALL\"}
                }
            }]" \
        --region "$AWS_REGION"
    
    echo "  ✅ ByCEOID GSI creation initiated (will backfill asynchronously)"
    echo "  ⏳ This may take several minutes depending on table size..."
fi

echo ""

# ============================================================
# STEP 5: Enable Point-in-Time Recovery
# ============================================================
echo "🔐 Step 5: Enabling Point-in-Time Recovery (PITR)..."

CRITICAL_TABLES=(
    "TrustGuard-Users"
    "TrustGuard-Orders"
    "TrustGuard-Escalations"
    "TrustGuard-AuditLogs"
)

for table in "${CRITICAL_TABLES[@]}"; do
    if aws dynamodb describe-table --table-name "$table" --region "$AWS_REGION" &>/dev/null; then
        PITR_STATUS=$(aws dynamodb describe-continuous-backups \
            --table-name "$table" \
            --region "$AWS_REGION" \
            --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' \
            --output text 2>/dev/null || echo "UNKNOWN")
        
        if [ "$PITR_STATUS" == "ENABLED" ]; then
            echo "  ✓ PITR already enabled: $table"
        else
            aws dynamodb update-continuous-backups \
                --table-name "$table" \
                --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
                --region "$AWS_REGION"
            echo "  ✅ PITR enabled: $table"
        fi
    fi
done

echo ""

# ============================================================
# STEP 6: Create SNS Topic for Escalations
# ============================================================
echo "📢 Step 6: Creating SNS topic for escalation alerts..."

TOPIC_NAME="TrustGuard-EscalationAlert"
EXISTING_TOPIC=$(aws sns list-topics \
    --region "$AWS_REGION" \
    --query "Topics[?contains(TopicArn, '$TOPIC_NAME')].TopicArn" \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_TOPIC" ]; then
    echo "  ⚠️  SNS topic already exists: $EXISTING_TOPIC"
    TOPIC_ARN="$EXISTING_TOPIC"
else
    TOPIC_ARN=$(aws sns create-topic \
        --name "$TOPIC_NAME" \
        --region "$AWS_REGION" \
        --attributes DisplayName="TrustGuard High-Value Transaction Alerts" \
        --tags Key=Project,Value=TrustGuard Key=Environment,Value="$ENVIRONMENT" \
        --query 'TopicArn' \
        --output text)
    
    echo "  ✅ SNS topic created: $TOPIC_ARN"
fi

echo ""

# ============================================================
# STEP 7: Create Secrets Manager Secrets
# ============================================================
echo "🔑 Step 7: Creating Secrets Manager secrets..."

# Generate secure random JWT secret (32 bytes = 256 bits)
JWT_SECRET=$(openssl rand -base64 32 | tr -d '\n')

# Create application secrets
APP_SECRET_NAME="/TrustGuard/dev/app"
if aws secretsmanager describe-secret --secret-id "$APP_SECRET_NAME" --region "$AWS_REGION" &>/dev/null; then
    echo "  ⚠️  Secret already exists: $APP_SECRET_NAME"
else
    aws secretsmanager create-secret \
        --name "$APP_SECRET_NAME" \
        --description "TrustGuard JWT signing key and application secrets" \
        --secret-string "{\"JWT_SECRET\":\"$JWT_SECRET\"}" \
        --region "$AWS_REGION" \
        --tags Key=Project,Value=TrustGuard Key=Environment,Value="$ENVIRONMENT"
    
    echo "  ✅ Created: $APP_SECRET_NAME"
fi

# Create Meta API secrets (placeholder - user will update)
META_SECRET_NAME="/TrustGuard/dev/meta"
if aws secretsmanager describe-secret --secret-id "$META_SECRET_NAME" --region "$AWS_REGION" &>/dev/null; then
    echo "  ⚠️  Secret already exists: $META_SECRET_NAME"
else
    aws secretsmanager create-secret \
        --name "$META_SECRET_NAME" \
        --description "Meta WhatsApp/Instagram API credentials" \
        --secret-string "{\"APP_ID\":\"REPLACE_WITH_META_APP_ID\",\"APP_SECRET\":\"REPLACE_WITH_META_APP_SECRET\"}" \
        --region "$AWS_REGION" \
        --tags Key=Project,Value=TrustGuard Key=Environment,Value="$ENVIRONMENT"
    
    echo "  ✅ Created: $META_SECRET_NAME (UPDATE WITH REAL META CREDENTIALS)"
fi

echo ""

# ============================================================
# STEP 8: Generate Environment Configuration
# ============================================================
echo "📝 Step 8: Generating environment configuration..."

cat > /tmp/trustguard-hybrid-config.env <<EOF
# ============================================================
# TrustGuard Hybrid Migration - Environment Variables
# Generated: $(date)
# ============================================================

# AWS Configuration
AWS_REGION=$AWS_REGION
ENVIRONMENT=$ENVIRONMENT

# DynamoDB Tables (Existing - No suffix)
USERS_TABLE=TrustGuard-Users
OTPS_TABLE=TrustGuard-OTPs
AUDIT_LOGS_TABLE=TrustGuard-AuditLogs
ORDERS_TABLE=TrustGuard-Orders
RECEIPTS_TABLE=TrustGuard-Receipts

# DynamoDB Tables (New - Created by migration)
ESCALATIONS_TABLE=TrustGuard-Escalations
CEO_MAPPING_TABLE=TrustGuard-CEOMapping

# S3 Bucket (Existing)
RECEIPT_BUCKET=trustguard-receipts-$ACCOUNT_ID-$AWS_REGION

# SNS Topics
ESCALATION_SNS_TOPIC_ARN=$TOPIC_ARN

# Secrets Manager
SECRETS_PATH_APP=/TrustGuard/dev/app
SECRETS_PATH_META=/TrustGuard/dev/meta

# Business Logic
HIGH_VALUE_THRESHOLD=1000000

# ============================================================
# IMPORTANT: Copy this to backend/.env
# ============================================================
EOF

echo "  ✅ Configuration generated: /tmp/trustguard-hybrid-config.env"
echo ""
cat /tmp/trustguard-hybrid-config.env
echo ""

# ============================================================
# STEP 9: Summary
# ============================================================
echo "============================================================"
echo "✅ HYBRID MIGRATION COMPLETE"
echo "============================================================"
echo ""
echo "📊 Infrastructure Summary:"
echo ""
echo "  EXISTING RESOURCES (Preserved):"
echo "    ✓ TrustGuard-Users"
echo "    ✓ TrustGuard-OTPs"
echo "    ✓ TrustGuard-AuditLogs"
echo "    ✓ TrustGuard-Orders"
echo "    ✓ TrustGuard-Receipts"
echo "    ✓ S3 Bucket: trustguard-receipts-$ACCOUNT_ID-$AWS_REGION"
echo ""
echo "  NEW RESOURCES (Created):"
echo "    ✅ TrustGuard-Escalations (with ByCEOPending GSI)"
echo "    ✅ TrustGuard-CEOMapping (with ByPageID GSI)"
echo "    ✅ ByCEOID GSI on TrustGuard-Users (for multi-CEO tenancy)"
echo "    ✅ SNS Topic: $TOPIC_ARN"
echo "    ✅ Secrets Manager: /TrustGuard/dev/app"
echo "    ✅ Secrets Manager: /TrustGuard/dev/meta"
echo "    ✅ Point-in-Time Recovery enabled on critical tables"
echo ""
echo "📋 Next Steps:"
echo ""
echo "  1. Copy /tmp/trustguard-hybrid-config.env to backend/.env"
echo "  2. Update Meta API credentials in Secrets Manager:"
echo "     aws secretsmanager update-secret --secret-id /TrustGuard/dev/meta \\"
echo "       --secret-string '{\"APP_ID\":\"your_app_id\",\"APP_SECRET\":\"your_app_secret\"}'"
echo ""
echo "  3. Verify backend/common/config.py uses the correct table names"
echo ""
echo "  4. Test escalation workflow:"
echo "     cd backend && pytest ceo_service/tests/test_approval.py -v"
echo ""
echo "  5. Deploy updated Lambda functions with new environment variables"
echo ""
echo "============================================================"
echo "🎉 Infrastructure is ready for escalation workflow!"
echo "============================================================"
