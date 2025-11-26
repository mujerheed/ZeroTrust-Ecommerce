#!/bin/bash
# Quick AWS Setup for TrustGuard Production
# Run this after configuring AWS CLI

set -e

echo "🚀 TrustGuard AWS Quick Setup"
echo "=============================="
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured!"
    echo "Run: aws configure"
    exit 1
}

echo "✅ AWS credentials OK"
echo ""

# Create DynamoDB tables
echo "📊 Creating DynamoDB tables..."

aws dynamodb create-table \
  --table-name TrustGuard-Users-Prod \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  2>/dev/null && echo "✅ Users table created" || echo "ℹ️  Users table already exists"

aws dynamodb create-table \
  --table-name TrustGuard-Orders-Prod \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  2>/dev/null && echo "✅ Orders table created" || echo "ℹ️  Orders table already exists"

aws dynamodb create-table \
  --table-name TrustGuard-OTPs-Prod \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=request_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=request_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  2>/dev/null && echo "✅ OTPs table created" || echo "ℹ️  OTPs table already exists"

echo ""

# Create S3 bucket
echo "📦 Creating S3 bucket..."

BUCKET_NAME="trustguard-receipts-prod-$(date +%s)"

aws s3 mb s3://$BUCKET_NAME --region us-east-1 2>/dev/null && {
    echo "✅ S3 bucket created: $BUCKET_NAME"
    
    # Enable encryption
    aws s3api put-bucket-encryption \
      --bucket $BUCKET_NAME \
      --server-side-encryption-configuration '{
        "Rules": [{
          "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
          }
        }]
      }'
    
    echo "✅ Encryption enabled"
    
    # Save bucket name
    echo "S3_BUCKET_NAME=$BUCKET_NAME" >> .env.production
    
} || echo "ℹ️  S3 bucket already exists or error occurred"

echo ""

# Configure SNS
echo "📱 Configuring SNS for SMS..."

aws sns set-sms-attributes \
  --attributes DefaultSMSType=Transactional \
  --region us-east-1

echo "✅ SNS configured"
echo ""

# Summary
echo "=============================="
echo "✅ AWS Setup Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "1. Verify email in AWS SES Console"
echo "2. Update .env with Meta credentials"
echo "3. Configure Meta webhooks"
echo "4. Test with real phone numbers"
echo ""
echo "S3 Bucket: $BUCKET_NAME"
echo ""
