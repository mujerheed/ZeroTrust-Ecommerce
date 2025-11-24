#!/bin/bash
# Quick Setup Script for Receipt Preview & Notification Preferences

echo "🚀 Setting up Receipt Preview & Notification Preferences..."
echo ""

# Step 1: Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install @radix-ui/react-switch

# Step 2: Check if backend is running
echo ""
echo "🔍 Checking backend status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running. Starting backend..."
    cd ../backend
    uvicorn app:app --reload --port 8000 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    cd ../frontend
fi

# Step 3: Start frontend dev server
echo ""
echo "🌐 Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Quick Testing Guide:"
echo ""
echo "1️⃣  Receipt Preview Test:"
echo "   - Navigate to: http://localhost:3000/ceo/approvals"
echo "   - Click the 📄 button on any approval row"
echo "   - Verify receipt image loads with zoom controls"
echo "   - Check for mismatch warnings (orange/red alerts)"
echo "   - Test download button"
echo ""
echo "2️⃣  Notification Preferences Test:"
echo "   - Navigate to: http://localhost:3000/ceo/settings"
echo "   - Click the 'Notifications' tab"
echo "   - Toggle the 5 switches (SMS, Email, Push)"
echo "   - Click 'Save Notification Preferences'"
echo "   - Verify toast: 'Notification preferences saved successfully!'"
echo "   - Refresh page, toggles should persist"
echo ""
echo "3️⃣  Backend Endpoints:"
echo "   - Receipt: GET http://localhost:8000/ceo/orders/{order_id}/receipt"
echo "   - Notifications: PATCH http://localhost:8000/ceo/settings/notifications"
echo ""
echo "🛑 To stop servers:"
echo "   - Frontend: kill $FRONTEND_PID"
echo "   - Backend: kill $BACKEND_PID (if started by this script)"
echo ""
echo "📚 Documentation: docs/RECEIPT_AND_NOTIFICATIONS_IMPLEMENTATION.md"
