#!/bin/bash
set -e

# Navigate to the CloudFormation template directory
cd "$(dirname "$0")/../cloudformation"

echo "Validating template..."
sam validate --template-file trustguard-template.yaml

echo "Building the serverless application..."
# Attempt native build first; if it fails due to Python runtime mismatch, fallback to container build (requires Docker)
if ! sam build --template-file trustguard-template.yaml --build-dir ./build; then
  echo "Native build failed. Falling back to container build (ensure Docker is running)..."
  sam build --use-container --template-file trustguard-template.yaml --build-dir ./build
fi

echo "Deploying the CloudFormation stack..."
# Use saved config (samconfig.toml in cloudformation directory) or run guided setup
if [ -f samconfig.toml ]; then
  echo "Using saved configuration..."
  sam deploy
else
  echo "First deployment - running guided setup..."
  sam deploy --guided \
    --stack-name TrustGuard-Dev \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment=dev HighValueThreshold=1000000 BucketNamePrefix=trustguard-receipts
fi

echo "Deployment completed successfully!"
