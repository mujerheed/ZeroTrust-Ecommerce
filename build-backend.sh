#!/bin/bash
# Simplified Build - Backend Only (Frontend can be built separately)

set -e

echo "🚀 TrustGuard Backend Deployment Package"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce"
DEPLOY_DIR="$PROJECT_ROOT/deployment-backend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Clean and create deployment directory
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"/{backend,docs,scripts}

echo "📦 Building Backend Package..."
cd "$PROJECT_ROOT/backend"

# Copy source code
cp -r auth_service order_service integrations common "$DEPLOY_DIR/backend/"
cp app.py requirements.txt "$DEPLOY_DIR/backend/"

# Create .env template
cat > "$DEPLOY_DIR/backend/.env.production" << 'EOF'
# Environment
ENVIRONMENT=production

# AWS Configuration
AWS_REGION=us-east-1
USERS_TABLE=TrustGuard-Users-Prod
ORDERS_TABLE=TrustGuard-Orders-Prod
OTPS_TABLE=TrustGuard-OTPs-Prod
S3_BUCKET_NAME=trustguard-receipts-prod

# Meta WhatsApp (Replace with your values)
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN=YOUR_ACCESS_TOKEN

# Meta Instagram (Replace with your values)
INSTAGRAM_PAGE_ID=YOUR_PAGE_ID
INSTAGRAM_ACCESS_TOKEN=YOUR_ACCESS_TOKEN

# Meta App Secret (Replace with your value)
META_APP_SECRET=YOUR_APP_SECRET

# JWT Secret (Generate with: openssl rand -hex 32)
JWT_SECRET_KEY=GENERATE_RANDOM_SECRET_HERE
EOF

echo "✅ Backend source copied"

echo ""
echo "📦 Creating Lambda Deployment Package..."

# Create package directory
mkdir -p "$DEPLOY_DIR/backend/lambda-package"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt -t "$DEPLOY_DIR/backend/lambda-package/" --quiet --no-cache-dir

# Copy source files
cp -r auth_service order_service integrations common app.py "$DEPLOY_DIR/backend/lambda-package/"

# Create Lambda handler
cat > "$DEPLOY_DIR/backend/lambda-package/lambda_handler.py" << 'EOF'
from mangum import Mangum
from app import app

handler = Mangum(app)
EOF

# Create zip
cd "$DEPLOY_DIR/backend/lambda-package"
zip -r ../lambda-deployment.zip . -q

echo "✅ Lambda package created ($(du -h ../lambda-deployment.zip | cut -f1))"

echo ""
echo "📦 Copying Documentation..."
cp -r "$PROJECT_ROOT/.gemini/antigravity/brain/683bba3c-47ea-4100-a86a-194ac18119d9"/*.md "$DEPLOY_DIR/docs/" 2>/dev/null || true
echo "✅ Documentation copied ($(ls -1 "$DEPLOY_DIR/docs" | wc -l) files)"

echo ""
echo "📦 Creating Deployment Scripts..."

# AWS deployment script
cat > "$DEPLOY_DIR/scripts/1-deploy-aws-infrastructure.sh" << 'EOFAWS'
#!/bin/bash
# Deploy AWS Infrastructure

set -e

echo "🚀 Deploying AWS Infrastructure..."

# Check AWS credentials
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured!"
    echo "Run: aws configure"
    exit 1
}

echo "✅ AWS credentials verified"

# Create DynamoDB tables
echo ""
echo "📊 Creating DynamoDB tables..."

aws dynamodb create-table \
  --table-name TrustGuard-Users-Prod \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 2>/dev/null && echo "✅ Users table created" || echo "ℹ️  Users table exists"

aws dynamodb create-table \
  --table-name TrustGuard-Orders-Prod \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 2>/dev/null && echo "✅ Orders table created" || echo "ℹ️  Orders table exists"

aws dynamodb create-table \
  --table-name TrustGuard-OTPs-Prod \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=request_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=request_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 2>/dev/null && echo "✅ OTPs table created" || echo "ℹ️  OTPs table exists"

# Create S3 bucket
echo ""
echo "📦 Creating S3 bucket..."
BUCKET="trustguard-receipts-prod-$(date +%s)"
aws s3 mb s3://$BUCKET --region us-east-1 && {
    aws s3api put-bucket-encryption \
      --bucket $BUCKET \
      --server-side-encryption-configuration '{
        "Rules": [{
          "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
          }
        }]
      }'
    echo "✅ S3 bucket created: $BUCKET"
    echo "S3_BUCKET_NAME=$BUCKET" >> ../backend/.env.production
} || echo "ℹ️  S3 bucket creation skipped"

# Configure SNS
echo ""
echo "📱 Configuring SNS for SMS..."
aws sns set-sms-attributes \
  --attributes DefaultSMSType=Transactional \
  --region us-east-1
echo "✅ SNS configured"

echo ""
echo "=========================================="
echo "✅ AWS Infrastructure Deployed!"
echo "=========================================="
echo ""
echo "Next: Run 2-deploy-lambda.sh"
EOFAWS

chmod +x "$DEPLOY_DIR/scripts/1-deploy-aws-infrastructure.sh"

# Lambda deployment script
cat > "$DEPLOY_DIR/scripts/2-deploy-lambda.sh" << 'EOFLAMBDA'
#!/bin/bash
# Deploy Lambda Function

set -e

echo "🚀 Deploying Lambda Function..."

# Check if lambda-deployment.zip exists
if [ ! -f "../backend/lambda-deployment.zip" ]; then
    echo "❌ lambda-deployment.zip not found!"
    exit 1
fi

# Create Lambda function
aws lambda create-function \
  --function-name TrustGuard-API-Prod \
  --runtime python3.11 \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role \
  --handler lambda_handler.handler \
  --zip-file fileb://../backend/lambda-deployment.zip \
  --timeout 30 \
  --memory-size 512 \
  --region us-east-1 \
  --environment Variables="{$(cat ../backend/.env.production | grep -v '^#' | grep '=' | sed 's/^/"/;s/=/":"/;s/$/",/' | tr '\n' ' ' | sed 's/, $//')}" \
  2>/dev/null && echo "✅ Lambda function created" || {
    echo "ℹ️  Lambda function exists, updating code..."
    aws lambda update-function-code \
      --function-name TrustGuard-API-Prod \
      --zip-file fileb://../backend/lambda-deployment.zip \
      --region us-east-1
    echo "✅ Lambda function updated"
  }

echo ""
echo "✅ Lambda Deployed!"
echo ""
echo "Next: Configure API Gateway and Meta webhooks"
EOFLAMBDA

chmod +x "$DEPLOY_DIR/scripts/2-deploy-lambda.sh"

# Create README
cat > "$DEPLOY_DIR/README.md" << 'EOFREADME'
# TrustGuard Backend Deployment Package

## Quick Start

### 1. Configure Environment

```bash
cd backend
nano .env.production
# Update with your Meta credentials
```

### 2. Deploy AWS Infrastructure

```bash
cd scripts
./1-deploy-aws-infrastructure.sh
```

### 3. Deploy Lambda Function

```bash
./2-deploy-lambda.sh
```

### 4. Configure Meta Webhooks

- WhatsApp: Point to your API Gateway URL + `/integrations/webhook/whatsapp`
- Instagram: Point to your API Gateway URL + `/integrations/webhook/instagram`

## Package Contents

- `backend/` - Source code and Lambda package
- `docs/` - Complete documentation
- `scripts/` - Deployment automation

## Documentation

See `docs/` folder for complete guides.
EOFREADME

echo ""
echo "📦 Creating Archive..."
cd "$PROJECT_ROOT"
tar -czf "trustguard-backend-$TIMESTAMP.tar.gz" -C "$DEPLOY_DIR" .

echo "✅ Archive created: trustguard-backend-$TIMESTAMP.tar.gz"

echo ""
echo "=========================================="
echo "✅ BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "📦 Deployment Package:"
echo "   Location: $DEPLOY_DIR"
echo "   Archive: trustguard-backend-$TIMESTAMP.tar.gz"
echo "   Size: $(du -h trustguard-backend-$TIMESTAMP.tar.gz | cut -f1)"
echo ""
echo "📋 Contents:"
echo "   - Backend source code"
echo "   - Lambda deployment zip ($(du -h "$DEPLOY_DIR/backend/lambda-deployment.zip" | cut -f1))"
echo "   - Documentation ($(ls -1 "$DEPLOY_DIR/docs" | wc -l) files)"
echo "   - Deployment scripts (2)"
echo ""
echo "🚀 Deploy Instructions:"
echo "   1. Extract: tar -xzf trustguard-backend-$TIMESTAMP.tar.gz"
echo "   2. Configure: Edit backend/.env.production"
echo "   3. Deploy: cd scripts && ./1-deploy-aws-infrastructure.sh"
echo "   4. Lambda: ./2-deploy-lambda.sh"
echo ""
echo "📖 See README.md for details"
echo ""
