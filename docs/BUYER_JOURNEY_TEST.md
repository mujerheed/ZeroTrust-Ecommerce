# Full Buyer Journey Test Guide

**Test Date:** December 8, 2025  
**Platform:** WhatsApp & Instagram  
**Status:** Ready for Testing

---

## 🎯 Complete Buyer Flow

This guide walks you through testing the entire TrustGuard buyer experience from registration to order completion.

---

## 📱 Step 1: Registration

### **Send Message:**
```
register
```

### **Expected Response:**
```
Hi [Your Name]! 👋

Welcome to TrustGuard! 🛡️

Let's get you set up.

What's your full name? 👤
```

### **Your Reply:**
```
John Doe
```

### **Expected Response:**
```
Thanks, John Doe! 📍

What's your delivery address?
```

### **Your Reply:**
```
123 Ikeja Road, Lagos, Nigeria
```

### **Expected Response (WhatsApp):**
```
🔐 TrustGuard Security Code

Your verification code is:

*ABC12345*

⏱ Valid for 5 minutes
🚫 Do not share this code with anyone

This code is for order verification only.
```

---

## 🔐 Step 2: OTP Verification

### **Send the OTP:**
```
verify ABC12345
```

**OR just send the code directly:**
```
ABC12345
```

### **Expected Response:**
```
✅ Verification Successful!

Your account is now active! 🎉

You can now:
• Place orders
• Upload receipts
• Track deliveries

Type 'help' to see all commands
```

---

## 📋 Step 3: Check Available Commands

### **Send Message:**
```
help
```

### **Expected Response:**
```
🛡️ TrustGuard Help

Available Commands:

📝 Registration & Account
• register - Create new account
• verify <code> - Verify your OTP

📦 Orders
• order <order_id> - Check order status
• confirm <order_id> - Confirm pending order
• cancel <order_id> - Cancel pending order

📸 Receipts
• upload - Get receipt upload instructions

📍 Address
• address - Update delivery address

❓ Help
• help - Show this message

---

Need more help?
Just message us anytime! We're here to assist. 💬

TrustGuard - Your Shopping Security Partner
```

---

## 🛒 Step 4: Create Order (Via Vendor)

**Note:** Orders are created by vendors, not buyers directly via chat.

### **Simulate Order Creation:**

1. **Go to Vendor Dashboard:** `http://localhost:3000/vendor/orders`
2. **Click "Create Order"**
3. **Fill in details:**
   - Buyer: Select the buyer you just registered
   - Product: "iPhone 14 Pro"
   - Amount: ₦500,000
   - Description: "Brand new, sealed box"
4. **Click "Create Order"**

### **Buyer Receives Notification:**
```
✅ Order Confirmed

Order ID: ord_abc123
Vendor: Tech Store Lagos
Amount: ₦500,000.00

Next Steps:
1. Make payment to vendor
2. Upload your payment receipt
3. Wait for verification
4. Delivery arranged ✈️

Type 'upload' for receipt upload instructions

Need help? Just ask! 💬
```

---

## 📊 Step 5: Check Order Status

### **Send Message:**
```
order ord_abc123
```

### **Expected Response:**
```
⏳ Order Status

Order ID: ord_abc123
Status: PENDING
Amount: ₦500,000.00

Need help? Type 'help' for commands
```

---

## 💰 Step 6: Make Payment & Upload Receipt

### **Option A: Via Chat (Get Upload Link)**

**Send Message:**
```
upload
```

**Expected Response:**
```
📸 Receipt Upload

To upload your payment receipt:

1. Make sure you have an active order
2. Your vendor will provide you with an upload link
3. Take a clear photo of your receipt
4. Click the link and upload

Need help? Just ask!

Type 'help' for other commands
```

### **Option B: Via Vendor Dashboard**

1. **Vendor generates upload link** for the order
2. **Buyer receives link via WhatsApp/Instagram**
3. **Buyer clicks link** → Opens upload page
4. **Buyer uploads receipt photo**

### **Option C: Direct Image Upload (WhatsApp)**

**Send a photo** of your payment receipt directly in WhatsApp

**Expected Response:**
```
📸 Receipt Received!

We've received your payment receipt.

Order ID: ord_abc123

Our team is verifying your payment. You'll be notified once verification is complete.

⏱ Verification usually takes 5-15 minutes

Thank you for using TrustGuard! 🛡️
```

---

## ✅ Step 7: Order Confirmation

**After vendor/CEO approves the order:**

### **Buyer Receives:**
```
✅ Payment Verified!

Order: ord_abc123

Your payment has been confirmed! 🎉

The vendor has been notified and will proceed with delivery.

Track your order:
Type 'order ord_abc123' anytime

Thank you for trusting TrustGuard! 🛡️
```

---

## 📦 Step 8: Track Order

### **Send Message:**
```
order ord_abc123
```

### **Expected Response:**
```
✅ Order Status

Order ID: ord_abc123
Status: CONFIRMED
Amount: ₦500,000.00

Need help? Type 'help' for commands
```

---

## 🔄 Step 9: Update Delivery Address

### **Send Message:**
```
address
```

### **Expected Response:**
```
📍 Your Current Address

123 Ikeja Road, Lagos, Nigeria

Would you like to update it?

Reply:
• 'yes' to keep current address
• 'update address to [new address]' to change
```

### **Your Reply:**
```
update address to 456 Victoria Island, Lagos, Nigeria
```

### **Expected Response:**
```
📍 Address Updated

New delivery address:
456 Victoria Island, Lagos, Nigeria

Is this address correct?

Reply:
• 'yes' to confirm and finalize order
• 'update address to [another address]' to change again
```

---

## ❌ Step 10: Cancel Order (Optional)

### **Send Message:**
```
cancel ord_abc123
```

### **Expected Response:**
```
Order cancellation processed.

Order ID: ord_abc123 has been cancelled.

Need help? Type 'help' for commands
```

---

## 🧪 Testing Checklist

### **Registration Flow:**
- [ ] Send `register` command
- [ ] Provide name when prompted
- [ ] Provide address when prompted
- [ ] Receive OTP via WhatsApp/Instagram
- [ ] Verify OTP successfully
- [ ] Receive confirmation message

### **Order Management:**
- [ ] Vendor creates order
- [ ] Buyer receives order notification
- [ ] Check order status with `order <id>`
- [ ] Confirm order with `confirm <id>`

### **Receipt Upload:**
- [ ] Request upload instructions with `upload`
- [ ] Upload receipt via link or direct image
- [ ] Receive upload confirmation

### **Address Management:**
- [ ] Check current address with `address`
- [ ] Update address successfully
- [ ] Confirm new address

### **Help & Support:**
- [ ] Get help with `help` command
- [ ] Test unknown commands (should get helpful response)

---

## 📊 Monitor Testing

### **Watch CloudWatch Logs:**
```bash
aws logs tail /aws/lambda/TrustGuard-CEOService-dev --follow --region us-east-1
```

### **Expected Log Entries:**
```
🔔 WHATSAPP WEBHOOK RECEIVED!
"WhatsApp message parsed" - sender: "234..."
"Processing message" - platform: "whatsapp"
"Detected intent: register"
"Conversation state saved: waiting_for_name"
"WhatsApp message sent" ✅
```

---

## 🎯 Success Criteria

**All tests pass if:**
1. ✅ Registration completes successfully
2. ✅ OTP sent and verified
3. ✅ Order notifications received
4. ✅ Order status can be checked
5. ✅ Receipt upload works
6. ✅ Address can be updated
7. ✅ Help command shows all options
8. ✅ All responses are timely (< 3 seconds)

---

## 🐛 Troubleshooting

### **No Response Received:**
- Check CloudWatch logs for errors
- Verify access tokens in Secrets Manager
- Check webhook configuration in Meta App Dashboard

### **OTP Not Received:**
- Check if phone number is correct
- Verify WhatsApp access token is valid
- Check CloudWatch for "OTP sent" log

### **Order Not Found:**
- Verify order was created in vendor dashboard
- Check order ID is correct
- Ensure buyer_id matches

---

## 📱 Test Platforms

### **WhatsApp:**
- Use Meta's sandbox test number
- Send messages from your personal WhatsApp
- All features should work

### **Instagram:**
- Send DM to your Instagram business account
- Registration flow includes phone number collection
- All features should work

---

**Happy Testing!** 🚀

If you encounter any issues, check CloudWatch logs and the troubleshooting section above.

---

**Last Updated:** December 8, 2025
