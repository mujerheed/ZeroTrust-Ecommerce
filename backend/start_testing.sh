#!/bin/bash
# TrustGuard E2E Testing - Quick Start Script

echo "🚀 TrustGuard E2E Testing Setup"
echo "================================"
echo ""

# Navigate to backend
cd "/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce/backend"

# Check Python dependencies
echo "📦 Checking dependencies..."
python3 -c "import reportlab, qrcode, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies. Installing..."
    pip3 install --break-system-packages reportlab qrcode pillow 2>&1 | tail -5
fi

# Clear port 8000
echo "🔧 Clearing port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start backend server
echo "🌐 Starting backend server on port 8000..."
echo ""
echo "Server will start in background. Check logs with:"
echo "  tail -f /tmp/trustguard_server.log"
echo ""

nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload > /tmp/trustguard_server.log 2>&1 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo ""

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
for i in {1..10}; do
    sleep 1
    curl -s http://localhost:8000/ > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Server is ready!"
        echo ""
        break
    fi
    echo -n "."
done

# Test server health
echo "🏥 Testing server health..."
HEALTH=$(curl -s http://localhost:8000/)
echo "$HEALTH"
echo ""

# Show Meta credentials
echo "🔑 Meta API Credentials:"
python3 -c "
from common.config import settings
print(f'  WhatsApp Phone ID: {settings.WHATSAPP_PHONE_NUMBER_ID}')
print(f'  Instagram Page ID: {settings.INSTAGRAM_PAGE_ID}')
print(f'  Environment: {settings.ENVIRONMENT}')
"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete! Ready for E2E Testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Next Steps:"
echo "  1. Test CEO Registration: python3 test_ceo_registration.py"
echo "  2. Test WhatsApp Flow: Send 'hi' to your WhatsApp Business number"
echo "  3. Test Instagram Flow: Send 'hi' to your Instagram page"
echo ""
echo "📊 Monitor logs:"
echo "  tail -f /tmp/trustguard_server.log"
echo ""
echo "🛑 Stop server:"
echo "  kill $SERVER_PID"
echo ""
