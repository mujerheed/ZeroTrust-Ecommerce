#!/bin/bash
set -e

# Navigate to the CloudFormation template directory
cd "$(dirname "$0")/../cloudformation"

echo "Validating template..."
sam validate --template-file trustguard-template.yaml

echo "Building the serverless application..."
sam build --template-file trustguard-template.yaml --build-dir ./build

echo "Deploying the CloudFormation stack..."
sam deploy --guided \
  --template-file ./build/template.yaml \
  --stack-name TrustGuard-Dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset \
  --parameter-overrides BucketNamePrefix=trustguard-receipts

echo "Deployment completed successfully!"
