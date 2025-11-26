#!/bin/bash
# Complete Build and Deployment Package Creator
# Creates production-ready deployment packages

set -e

echo "🚀 TrustGuard Production Build & Deployment Package"
echo "===================================================="
echo ""

PROJECT_ROOT="/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce"
DEPLOY_DIR="$PROJECT_ROOT/deployment"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Clean and create deployment directory
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"/{backend,frontend,docs}

echo "📦 Step 1: Building Backend Package..."
cd "$PROJECT_ROOT/backend"

# Create backend deployment package
mkdir -p "$DEPLOY_DIR/backend/package"

# Copy source code
cp -r auth_service order_service integrations common "$DEPLOY_DIR/backend/"
cp app.py requirements.txt "$DEPLOY_DIR/backend/"
cp -r .env* "$DEPLOY_DIR/backend/" 2>/dev/null || true

# Create .env template
cat > "$DEPLOY_DIR/backend/.env.template" << 'EOF'
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

echo "✅ Backend package created"

echo ""
echo "📦 Step 2: Building Frontend..."
cd "$PROJECT_ROOT/frontend"

# Build frontend
echo "Building Next.js production bundle..."
npm run build

# Copy build output
cp -r .next "$DEPLOY_DIR/frontend/"
cp -r public "$DEPLOY_DIR/frontend/"
cp package.json package-lock.json next.config.ts "$DEPLOY_DIR/frontend/"

# Create frontend .env template
cat > "$DEPLOY_DIR/frontend/.env.production.template" << 'EOF'
NEXT_PUBLIC_API_URL=https://api.trustguard.ng
NEXT_PUBLIC_ENVIRONMENT=production
EOF

echo "✅ Frontend build complete"

echo ""
echo "📦 Step 3: Creating Lambda Deployment Package..."
cd "$DEPLOY_DIR/backend"

# Install dependencies
pip3 install -r requirements.txt -t package/ --quiet

# Create zip
cd package
zip -r ../lambda-deployment.zip . -q
cd ..
zip -g lambda-deployment.zip *.py -q
zip -rg lambda-deployment.zip auth_service/ order_service/ integrations/ common/ -q

echo "✅ Lambda package created: lambda-deployment.zip"

echo ""
echo "📦 Step 4: Copying Documentation..."
cp "$PROJECT_ROOT/.gemini/antigravity/brain/683bba3c-47ea-4100-a86a-194ac18119d9"/*.md "$DEPLOY_DIR/docs/" 2>/dev/null || true

echo "✅ Documentation copied"

echo ""
echo "📦 Step 5: Creating Deployment Scripts..."

# AWS deployment script
cat > "$DEPLOY_DIR/deploy-to-aws.sh" << 'EOFAWS'
#!/bin/bash
# Deploy TrustGuard to AWS

set -e

echo "🚀 Deploying TrustGuard to AWS..."

# Check AWS credentials
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured!"
    exit 1
}

# Create DynamoDB tables
echo "Creating DynamoDB tables..."
aws dynamodb create-table \
  --table-name TrustGuard-Users-Prod \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 2>/dev/null || echo "Table exists"

aws dynamodb create-table \
  --table-name TrustGuard-Orders-Prod \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 2>/dev/null || echo "Table exists"

aws dynamodb create-table \
  --table-name TrustGuard-OTPs-Prod \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=request_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=request_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 2>/dev/null || echo "Table exists"

# Create S3 bucket
BUCKET="trustguard-receipts-prod-$(date +%s)"
aws s3 mb s3://$BUCKET --region us-east-1
aws s3api put-bucket-encryption \
  --bucket $BUCKET \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

echo "✅ AWS resources created!"
echo "S3 Bucket: $BUCKET"
echo ""
echo "Next: Upload lambda-deployment.zip to Lambda"
EOFAWS

chmod +x "$DEPLOY_DIR/deploy-to-aws.sh"

# Create README
cat > "$DEPLOY_DIR/README.md" << 'EOFREADME'
# TrustGuard Production Deployment Package

## Contents

- `backend/` - Backend source code and Lambda package
- `frontend/` - Frontend build output
- `docs/` - Complete documentation
- `deploy-to-aws.sh` - AWS deployment script

## Quick Start

### 1. Configure Environment

```bash
cd backend
cp .env.template .env
# Edit .env with your credentials
```

### 2. Deploy to AWS

```bash
./deploy-to-aws.sh
```

### 3. Deploy Lambda

```bash
aws lambda create-function \
  --function-name TrustGuard-API-Prod \
  --runtime python3.11 \
  --role YOUR_LAMBDA_ROLE_ARN \
  --handler main.handler \
  --zip-file fileb://backend/lambda-deployment.zip \
  --timeout 30 \
  --memory-size 512
```

### 4. Deploy Frontend

```bash
cd frontend
npm install
npm start
# Or deploy to S3 + CloudFront
```

## Documentation

See `docs/` folder for:
- Production deployment guide
- Quick-start guide
- Feature coverage report
- Testing guides
- And more...

## Support

Check documentation or server logs for troubleshooting.
EOFREADME

echo ""
echo "📦 Step 6: Creating Archive..."
cd "$PROJECT_ROOT"
tar -czf "trustguard-deployment-$TIMESTAMP.tar.gz" -C "$DEPLOY_DIR" .

echo "✅ Deployment archive created: trustguard-deployment-$TIMESTAMP.tar.gz"

echo ""
echo "===================================================="
echo "✅ BUILD COMPLETE!"
echo "===================================================="
echo ""
echo "📦 Deployment Package Location:"
echo "   $DEPLOY_DIR"
echo ""
echo "📦 Archive:"
echo "   $PROJECT_ROOT/trustguard-deployment-$TIMESTAMP.tar.gz"
echo ""
echo "📋 Package Contents:"
echo "   - Backend source code"
echo "   - Lambda deployment zip ($(du -h "$DEPLOY_DIR/backend/lambda-deployment.zip" | cut -f1))"
echo "   - Frontend production build"
echo "   - Complete documentation ($(ls -1 "$DEPLOY_DIR/docs" | wc -l) files)"
echo "   - Deployment scripts"
echo ""
echo "🚀 Next Steps:"
echo "   1. Extract archive on deployment server"
echo "   2. Configure .env files"
echo "   3. Run ./deploy-to-aws.sh"
echo "   4. Deploy Lambda function"
echo "   5. Configure Meta webhooks"
echo ""
echo "📖 See deployment/README.md for details"
echo ""
