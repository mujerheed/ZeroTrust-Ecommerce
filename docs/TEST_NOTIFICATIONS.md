# 🧪 Testing the Notification System

## Quick Test Guide

### Method 1: Using the Test Endpoint (Easiest) ⚡

**Step 1: Make sure backend is running**
```bash
cd backend
./venv/bin/uvicorn app:app --reload --port 8000
```

**Step 2: Make sure frontend is running**
```bash
cd frontend
npm run dev
```

**Step 3: Login to CEO portal**
- Go to `http://localhost:3000/ceo/login`
- Login with your CEO credentials
- You should see the dashboard

**Step 4: Open browser console (F12) and run this:**
```javascript
// Get your auth token
const token = localStorage.getItem('token');

// Create a test escalation notification
fetch('http://localhost:8000/ceo/test/create-notification?notification_type=escalation', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => {
  console.log('✅ Test notification created!', data);
  alert('Test notification created! Wait up to 30 seconds for the modal to pop up.');
});
```

**Step 5: What should happen:**
1. ✅ Within 30 seconds (next poll cycle), the EscalationModal should auto-pop
2. ✅ Notification bell in TopBar should show unread count badge
3. ✅ Toast notification appears: "New escalation requires your attention!"
4. ✅ Click bell icon to see notification in dropdown

---

### Method 2: Using cURL (From Terminal) 🔧

**Step 1: Get your JWT token**
- Login to CEO portal
- Open browser DevTools → Application → Local Storage
- Copy the value of `token`

**Step 2: Create test notification**
```bash
# Replace YOUR_JWT_TOKEN with the actual token
curl -X POST "http://localhost:8000/ceo/test/create-notification?notification_type=escalation" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Test notification created successfully! Check your notification bell in TopBar.",
  "data": {
    "notification": {
      "id": "notif_1234567890_abc123",
      "type": "escalation",
      "title": "🧪 TEST: High-Value Transaction",
      "message": "Test order #test_order_12 (₦1,200,000) requires your approval",
      "order_id": "test_order_1234567890_5678",
      "amount": 1200000,
      "reason": "HIGH_VALUE"
    },
    "instructions": {
      "1": "Check the notification bell icon in TopBar (should show unread count)",
      "2": "If type=escalation, the modal should auto-pop within 30 seconds",
      "3": "Click the bell to see the notification in the dropdown",
      "4": "Click 'Review Now' to test navigation to approvals page"
    }
  }
}
```

---

### Method 3: Using Postman 📬

**Setup:**
1. Create new POST request
2. URL: `http://localhost:8000/ceo/test/create-notification?notification_type=escalation`
3. Headers: 
   - Key: `Authorization`
   - Value: `Bearer YOUR_JWT_TOKEN`
4. Click "Send"

**Try different notification types:**
- `notification_type=escalation` → Auto-pops modal
- `notification_type=alert` → Shows in bell, no auto-pop
- `notification_type=info` → Shows in bell, no auto-pop

---

## Expected Behavior ✅

### When you create an escalation notification:

**Immediate (on API response):**
- ✅ Backend creates notification in database
- ✅ Returns success message with notification details

**Within 30 seconds (next poll):**
- ✅ TopBar fetches notifications via `/ceo/notifications`
- ✅ Detects new escalation (type=escalation, unread=true)
- ✅ EscalationModal auto-pops with:
  - Order ID (truncated)
  - Amount (₦1,200,000)
  - Reason badge (High-Value Transaction or Vendor Flagged)
  - 15-second auto-close countdown
  - "Review Now" button
- ✅ Toast notification: "New escalation requires your attention!"
- ✅ Red badge appears on bell icon with unread count

**When you interact:**
- ✅ Click notification in dropdown → Marks as read + navigates to Approvals
- ✅ Click "Review Now" in modal → Navigates to Approvals page
- ✅ Click "Dismiss" → Closes modal
- ✅ Unread count updates automatically

---

## Troubleshooting 🔧

### Modal not appearing?
- Check browser console for errors
- Verify TopBar is polling (should see network requests every 30s)
- Make sure notification type is "escalation"
- Try refreshing the page after creating notification

### Notification not showing in bell?
- Wait 30 seconds for next poll cycle
- Check `/ceo/notifications` endpoint in Network tab
- Verify JWT token is valid (not expired)

### API returns 401 Unauthorized?
- Your JWT token expired, login again
- Copy fresh token from localStorage

### API returns 500 error?
- Check backend terminal for Python errors
- Verify DynamoDB tables exist (USERS_TABLE)
- Check backend logs for specific error message

---

## Real-World Testing (Vendor Escalation) 🌍

To test with real vendor escalation flow:

1. **Create a high-value order** (≥ ₦1,000,000)
2. **Vendor flags the receipt**
3. **System automatically:**
   - Creates escalation record
   - Creates notification
   - Sends SMS/Email (if configured)
   - Auto-pops modal in CEO portal

---

## Cleanup 🧹

Delete test notifications:
```javascript
// In browser console
const token = localStorage.getItem('token');

fetch('http://localhost:8000/ceo/notifications/read-all', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log('All notifications marked as read:', data));
```

---

## Success Indicators ✨

You'll know it's working when you see:
1. ✅ Modal pops up automatically (no manual action needed)
2. ✅ Countdown timer shows "Auto-closing in 15s"
3. ✅ Notification bell has red badge with count
4. ✅ Toast appears in bottom-right corner
5. ✅ Clicking notification navigates to Approvals page
6. ✅ Marking as read removes from unread count

---

**🎉 Congratulations!** If all these work, your real-time notification system is fully functional!
