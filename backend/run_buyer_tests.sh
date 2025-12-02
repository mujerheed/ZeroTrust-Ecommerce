#!/bin/bash
# Quick Buyer Flow Test Guide

echo "🧪 TrustGuard Buyer Flow Testing"
echo "================================="
echo ""
echo "This will test the complete buyer journey:"
echo "  1. CEO Registration"
echo "  2. Buyer Registration (WhatsApp)"
echo "  3. Order Creation"
echo "  4. Receipt Upload"
echo "  5. Order Status Check"
echo ""
echo "📋 Prerequisites:"
echo "  ✓ Python 3.11+"
echo "  ✓ Backend server running (port 8000)"
echo "  ✓ DynamoDB Local or AWS credentials"
echo ""
echo "🚀 Starting tests..."
echo ""

# Navigate to backend
cd "/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce/backend"

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend server not running!"
    echo ""
    echo "Starting server in background..."
    ./start_testing.sh &
    sleep 5
fi

echo "✅ Server is running"
echo ""
echo "📦 Test 1: Complete Buyer Flow (WhatsApp)"
echo "=========================================="
python3 test_complete_buyer_flow.py

echo ""
echo "📦 Test 2: Mock Webhook Test (Alternative)"
echo "=========================================="
echo "This simulates WhatsApp messages without Meta API"
python3 test_mock_webhooks.py

echo ""
echo "✅ All tests complete!"
echo ""
echo "📊 What was tested:"
echo "  ✓ CEO registration with OTP"
echo "  ✓ Buyer registration via WhatsApp"
echo "  ✓ OTP verification"
echo "  ✓ Order creation"
echo "  ✓ Receipt upload to S3"
echo "  ✓ Order status tracking"
echo ""
echo "🎯 Next steps:"
echo "  1. Check test output above for any errors"
echo "  2. Review generated PDFs in /tmp/"
echo "  3. Check DynamoDB tables for data"
echo "  4. Test vendor approval flow"
