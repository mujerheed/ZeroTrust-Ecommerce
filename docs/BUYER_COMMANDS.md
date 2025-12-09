# TrustGuard Buyer Commands Reference

**Last Updated:** December 8, 2025

Complete guide to all commands available to buyers via WhatsApp and Instagram messaging.

---

## 📱 Quick Command List

```
• register - Create new account
• verify <code> - Verify OTP code
• order <order_id> - Check order status
• confirm - Confirm pending order
• negotiate <order_id> <amount> - Request price negotiation
• accept counter - Accept vendor's counter-offer
• reject counter - Reject vendor's counter-offer
• address - Update delivery address
• upload - Get receipt upload instructions
• help - Show all commands
```

---

## 📋 Registration & Account

### `register`
**Description:** Start account registration process  
**Aliases:** `start`, `hi`, `hello`, `hey`, `begin`

**Flow:**
```
You: register
Bot: Hi [Name]! 👋
     Welcome to [Business Name]! 🛡️
     What's your full name? 👤

You: John Doe
Bot: Thanks, John Doe! 📍
     What's your delivery address?

You: 123 Ikeja Road, Lagos
Bot: [Sends OTP code]

You: ABC12345
Bot: ✅ Verification Successful!
```

---

### `verify <code>`
**Description:** Verify your OTP code  
**Format:** `verify ABC12345` or just `ABC12345`

**Example:**
```
You: verify ABC12345
Bot: ✅ Verification Successful!
     Your account is now active! 🎉
```

---

## 📦 Orders

### `order <order_id>`
**Description:** Check order status  
**Aliases:** `status <order_id>`

**Example:**
```
You: order ord_abc123
Bot: ⏳ Order Status
     
     Order ID: ord_abc123
     Status: PENDING
     Amount: ₦500,000.00
```

---

### `confirm`
**Description:** Confirm your pending order  
**Format:** `confirm` or `confirm <order_id>`

**Example:**
```
You: confirm
Bot: 📍 Delivery Address Confirmation
     
     Current address: 123 Ikeja Road, Lagos
     Is this correct?
     
     Reply 'yes' or 'update address to [new address]'

You: yes
Bot: ✅ Order Confirmed!
```

---

### `cancel <order_id>`
**Description:** Cancel an order

**Example:**
```
You: cancel ord_abc123
Bot: Order cancellation processed.
```

---

## 💰 Negotiation (NEW!)

### `negotiate <order_id> <amount>`
**Description:** Request price negotiation with vendor  
**Format:** `negotiate ord_123 450000`

**Example:**
```
You: negotiate ord_abc123 450000
Bot: 💬 Negotiation Request Sent
     
     Order: ord_abc123
     Original Price: ₦500,000.00
     Your Offer: ₦450,000.00
     
     The vendor will review your offer.
     You'll be notified when they respond.
```

**When vendor responds:**
```
Bot: 💰 Vendor Counter-Offer Received!
     
     Order: ord_abc123
     Your Offer: ₦450,000.00
     Vendor Counter: ₦475,000.00
     
     Reply:
     • 'accept counter' to accept ₦475,000
     • 'reject counter' to decline
```

---

### `accept counter`
**Description:** Accept vendor's counter-offer  
**Aliases:** `accept offer`

**Example:**
```
You: accept counter
Bot: ✅ Negotiation Accepted!
     
     Final Price: ₦475,000.00
     
     The order has been updated.
     Proceed with payment at the new price.
```

---

### `reject counter`
**Description:** Reject vendor's counter-offer  
**Aliases:** `reject offer`

**Example:**
```
You: reject counter
Bot: ❌ Counter-Offer Rejected
     
     You have declined the vendor's offer.
     
     You can:
     • Contact the vendor directly
     • Make a new offer
     • Proceed with the original price
```

---

## 📸 Receipts

### `upload`
**Description:** Get receipt upload instructions

**Example:**
```
You: upload
Bot: 📸 Receipt Upload
     
     To upload your payment receipt:
     1. Make sure you have an active order
     2. Your vendor will provide an upload link
     3. Take a clear photo
     4. Click the link and upload
```

### Direct Photo Upload
**Description:** Send receipt photo directly (WhatsApp/Instagram)

**Example:**
```
You: [Send photo of receipt]
Bot: ✅ Receipt Image Received!
     
     Your payment proof has been securely uploaded.
     
     📁 File: 20251208_123045_abc123.jpg
     📊 Status: Pending vendor verification
```

---

## 📍 Address Management

### `address`
**Description:** Update delivery address  
**Aliases:** `update address`, `my address`

**Example:**
```
You: address
Bot: 📍 Your Current Address
     
     123 Ikeja Road, Lagos
     
     Reply 'yes' to keep or 'update address to [new address]'

You: update address to 456 Victoria Island, Lagos
Bot: ✅ Address Updated
```

---

## ❓ Help & Support

### `help`
**Description:** Show all available commands  
**Aliases:** `?`

**Example:**
```
You: help
Bot: 🛡️ TrustGuard Help
     
     Available Commands:
     
     📝 Registration & Account
     • register - Create new account
     • verify <code> - Verify OTP
     
     📦 Orders
     • order <order_id> - Check status
     • confirm - Confirm order
     
     💰 Negotiation
     • negotiate <order_id> <amount> - Request negotiation
     • accept counter - Accept counter-offer
     • reject counter - Reject counter-offer
     
     📸 Receipts
     • upload - Upload instructions
     
     📍 Address
     • address - Update delivery address
     
     ❓ Help
     • help - Show this message
```

---

## 🎯 Common Workflows

### **Complete Buyer Journey:**

```
1. Registration
   You: register
   → Provide name, address
   → Receive & verify OTP

2. Order Creation (Vendor creates)
   → You receive notification

3. Order Confirmation
   You: confirm
   → Confirm delivery address

4. Negotiation (Optional)
   You: negotiate ord_123 450000
   → Vendor reviews
   → You: accept counter

5. Payment & Receipt
   → Make payment
   → Send receipt photo
   → Vendor verifies

6. Completion
   → Receive PDF summary
```

---

## 💡 Tips & Best Practices

### **For Negotiation:**
- ✅ Be reasonable with your offer
- ✅ Respond promptly to counter-offers
- ✅ Keep communication professional
- ❌ Don't negotiate after payment

### **For Receipt Upload:**
- ✅ Use good lighting
- ✅ Ensure all text is visible
- ✅ Avoid blurry photos
- ✅ Upload immediately after payment

### **For Orders:**
- ✅ Confirm delivery address before finalizing
- ✅ Keep order ID for reference
- ✅ Check status regularly
- ✅ Contact vendor for delivery updates

---

## 🔒 Security Notes

- **Never share your OTP** with anyone
- **Verify vendor identity** before payment
- **Keep payment receipts** for your records
- **Report suspicious activity** immediately

---

## 📞 Support

Need help? Just message us anytime!

**Available 24/7:**
- Type your question in natural language
- Use `help` command for quick reference
- Contact your vendor directly for order-specific issues

---

**TrustGuard - Your Shopping Security Partner** 🛡️

---

**Last Updated:** December 8, 2025
