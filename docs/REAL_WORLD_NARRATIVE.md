# TrustGuard Zero Trust System — Real-World Narrative
## 🌇 Lagos, 2025: The Story of Ada's Fashion & Tunde Electronics

**Document Purpose:** Dissertation-ready narrative showing how TrustGuard's Zero Trust architecture works in real informal e-commerce scenarios in Nigeria.

---

## 👥 **Characters**

| Name | Business | Role | Platform |
|------|----------|------|----------|
| **Ada Ogunleye** | Ada's Fashion (Lagos Mainland Market) | CEO + Self-Assigned Vendor | WhatsApp Business |
| **Tunde Adebayo** | Tunde Electronics (Oshodi Tech Hub) | CEO | Instagram Business |
| **Femi Adeyemi** | — | Vendor (under Tunde) | — |
| **Chinedu** | — | Buyer (new customer) | WhatsApp |
| **Amina** | — | Buyer (returning customer) | Instagram |
| **The Bot** | TrustGuard AI | Sessionless chatbot | WhatsApp + Instagram |

---

## 📱 **SCENARIO 1: Chinedu Buys Red Ankara Dress from Ada (WhatsApp)**

> *"I see dis ankara dress on Ada's WhatsApp status — I wan buy am!"*

### 🔍 **Stage 1: Discovery & Initial Contact**

**Real-World Action:**
- Chinedu scrolls through WhatsApp → sees Ada's status: *"🔥 Red Ankara Dress - ₦12,500"*
- Taps "DM" → sends: *"Hi, I want dis red ankara dress. How much?"*

**System Response (Zero Trust Begins):**
```
TrustGuard Bot (via Ada's WhatsApp Business):
"Welcome! I dey verify you first. Send your name and address."
```

**Chinedu replies:**
```
"Chinedu, 123 Lagos St, Ikeja"
```

**Backend Processing:**
```typescript
// Webhook receives message
const sender_id = "2348031234567"
const buyer_id = `wa_${sender_id}`
const ceo_id = "ada_fashion" // Mapped from phone_number_id

// Store in TrustGuard-Users
await DynamoDB.putItem({
  TableName: "TrustGuard-Users",
  Item: {
    user_id: buyer_id,
    role: "BUYER",
    ceo_id: ceo_id,
    name: "Chinedu",
    address: "123 Lagos St, Ikeja",
    platform: "whatsapp",
    created_at: Math.floor(Date.now() / 1000)
  }
})
```

**Audit Log Entry:**
```json
{
  "action": "BUYER_REGISTERED",
  "actor_id": "wa_2348031234567",
  "ceo_id": "ada_fashion",
  "timestamp": 1732370400,
  "details": {
    "platform": "whatsapp",
    "masked_phone": "+234***4567"
  }
}
```

---

### 🔐 **Stage 2: OTP Authentication (Sessionless)**

**System Action:**
```
TrustGuard Bot:
"Your OTP is B7#K9@P2 — enter am in chat. Expire in 5 min."
```

**Backend Processing:**
```typescript
// Generate 8-char OTP (alphanumeric + symbols)
const otp = generateOTP(8) // "B7#K9@P2"
const hashed = await pbkdf2(otp, salt, 10000, 64, 'sha512')

// Store in TrustGuard-OTPs (TTL 5 min)
await DynamoDB.putItem({
  TableName: "TrustGuard-OTPs",
  Item: {
    buyer_id: "wa_2348031234567",
    hashed_otp: hashed.toString('hex'),
    expires_at: Math.floor(Date.now() / 1000) + 300, // 5 min
    attempts: 0
  }
})

// Send OTP via WhatsApp DM (using Ada's token from Secrets Manager)
const token = await getSecretValue("/ceo/ada_fashion/meta")
await sendWhatsAppMessage({
  to: "2348031234567",
  text: `Your OTP is ${otp} — enter am in chat. Expire in 5 min.`,
  token: token.whatsapp_token
})
```

**Chinedu types:**
```
B7#K9@P2
```

**Verification:**
```typescript
// Hash input and compare
const inputHash = await pbkdf2("B7#K9@P2", salt, 10000, 64, 'sha512')
const storedOTP = await DynamoDB.getItem("TrustGuard-OTPs", { buyer_id })

if (crypto.timingSafeEqual(inputHash, storedOTP.hashed_otp)) {
  // ✅ Valid
  await DynamoDB.deleteItem("TrustGuard-OTPs", { buyer_id }) // Single-use
  
  // Log success
  await logAudit({
    action: "OTP_VERIFY_SUCCESS",
    actor_id: buyer_id,
    ceo_id: ceo_id
  })
  
  // Bot replies
  await sendWhatsAppMessage({
    to: "2348031234567",
    text: "✅ Verified! Now, send bank details for payment."
  })
}
```

**Audit Log Entry:**
```json
{
  "action": "OTP_VERIFY_SUCCESS",
  "actor_id": "wa_2348031234567",
  "ceo_id": "ada_fashion",
  "timestamp": 1732370460,
  "details": {
    "platform": "whatsapp",
    "attempts": 1
  }
}
```

---

### 💸 **Stage 3: Order Creation & Payment**

**System Action:**
```
TrustGuard Bot:
"Bank: First Bank | Acc: 1234567890 | Ref: TG-8891"
```

**Chinedu:**
- Opens First Bank app → transfers ₦12,500
- Screenshot of receipt → uploads via WhatsApp

**Backend Processing (Media Upload):**
```typescript
// Webhook receives media message
const media_url = webhook.entry[0].changes[0].value.messages[0].image.id

// Download media using Graph API
const mediaResponse = await axios.get(
  `https://graph.facebook.com/v19.0/${media_url}`,
  { headers: { Authorization: `Bearer ${token.whatsapp_token}` } }
)

// Generate S3 presigned PUT URL
const s3Key = `receipts/${ceo_id}/${buyer_id}/${order_id}/receipt.jpg`
const presignedUrl = await s3.getSignedUrl('putObject', {
  Bucket: 'trustguard-receipts-1234567890-dev',
  Key: s3Key,
  Expires: 300, // 5 min
  ServerSideEncryption: 'AES256'
})

// Upload to S3
await axios.put(presignedUrl, mediaResponse.data, {
  headers: { 'Content-Type': 'image/jpeg' }
})

// Calculate checksum
const checksum = crypto.createHash('sha256').update(mediaResponse.data).digest('hex')

// Store metadata in TrustGuard-Receipts
await DynamoDB.putItem({
  TableName: "TrustGuard-Receipts",
  Item: {
    receipt_id: `rcpt_${Date.now()}`,
    order_id: order_id,
    buyer_id: buyer_id,
    vendor_id: "ceo_ada_fashion", // Ada is self-assigned vendor
    ceo_id: ceo_id,
    s3_key: s3Key,
    checksum: checksum,
    uploaded_at: Math.floor(Date.now() / 1000),
    status: "UPLOADED"
  }
})

// Create order record
await DynamoDB.putItem({
  TableName: "TrustGuard-Orders",
  Item: {
    order_id: order_id,
    buyer_id: buyer_id,
    vendor_id: "ceo_ada_fashion",
    ceo_id: ceo_id,
    total_amount: 12500,
    status: "RECEIPT_UPLOADED",
    created_at: Math.floor(Date.now() / 1000)
  }
})
```

**Bot Reply:**
```
"Receipt received! Ada will check am now."
```

**Audit Log Entry:**
```json
{
  "action": "RECEIPT_UPLOADED",
  "actor_id": "wa_2348031234567",
  "ceo_id": "ada_fashion",
  "timestamp": 1732370520,
  "details": {
    "order_id": "order_abc123",
    "amount": 12500,
    "checksum": "sha256:abcd1234..."
  }
}
```

---

### ✅ **Stage 4: Vendor Verification (Ada's Dashboard)**

**Vendor Portal Notification:**
```typescript
// Real-time toast appears on Ada's screen
toast.info(
  "Receipt uploaded for Order #abc123",
  {
    description: "Amount: ₦12,500",
    action: {
      label: "Verify",
      onClick: () => router.push("/vendor/receipts")
    },
    duration: 10000
  }
)
```

**Ada clicks "Verify" → Dashboard shows:**
```
Order #abc123
Buyer: +234***4567 (Chinedu)
Amount: ₦12,500
Receipt Preview: [S3 image loads]
Auto-Checks:
  ✅ Amount match: ₦12,500
  ✅ Timestamp: 2h ago (valid)
  ⚠️ Textract not enabled (manual review)
```

**Ada clicks ✅ "Approve":**
```typescript
// Frontend calls API
await api.post(`/vendor/orders/${order_id}/verify`, {
  action: "approve",
  notes: "Payment confirmed via bank app"
})

// Backend processes
await DynamoDB.updateItem({
  TableName: "TrustGuard-Orders",
  Key: { order_id },
  UpdateExpression: "SET #status = :status, verified_at = :timestamp",
  ExpressionAttributeNames: { "#status": "status" },
  ExpressionAttributeValues: {
    ":status": "APPROVED",
    ":timestamp": Math.floor(Date.now() / 1000)
  }
})

// Log audit
await logAudit({
  action: "RECEIPT_APPROVED",
  actor_id: "ceo_ada_fashion",
  ceo_id: "ada_fashion",
  details: { order_id, amount: 12500 }
})

// Notify buyer via WhatsApp
await sendWhatsAppMessage({
  to: "2348031234567",
  text: "✅ Payment verified! Confirm address: 123 Lagos St, Ikeja? (Reply 'Yes' or send updated address)"
})
```

**Audit Log Entry:**
```json
{
  "action": "RECEIPT_APPROVED",
  "actor_id": "ceo_ada_fashion",
  "ceo_id": "ada_fashion",
  "timestamp": 1732377600,
  "details": {
    "order_id": "order_abc123",
    "amount": 12500,
    "vendor_notes": "Payment confirmed via bank app"
  }
}
```

---

### 📦 **Stage 5: Delivery Confirmation**

**Chinedu replies:**
```
Yes
```

**Bot generates PDF confirmation:**
```typescript
// Generate PDF with order details
const pdfBuffer = await generatePDF({
  order_id: order_id,
  buyer_name: "Chinedu",
  buyer_address: "123 Lagos St, Ikeja",
  items: [{ name: "Red Ankara Dress", qty: 1, price: 12500 }],
  total: 12500,
  vendor: "Ada's Fashion",
  status: "APPROVED"
})

// Upload to S3
const pdfKey = `confirmations/${ceo_id}/${order_id}/confirmation.pdf`
await s3.putObject({
  Bucket: 'trustguard-receipts-1234567890-dev',
  Key: pdfKey,
  Body: pdfBuffer,
  ContentType: 'application/pdf',
  ServerSideEncryption: 'AES256'
})

// Generate secure link (7-day expiry)
const secureLink = await s3.getSignedUrl('getObject', {
  Bucket: 'trustguard-receipts-1234567890-dev',
  Key: pdfKey,
  Expires: 604800 // 7 days
})

// Send to buyer
await sendWhatsAppMessage({
  to: "2348031234567",
  text: `Order Completed! Your ankara dress go reach you by Friday. Track here: ${secureLink}`
})
```

**Final Order Status:**
```
Status: APPROVED → CONFIRMED
Delivery ETA: Friday
PDF Generated: ✅
Audit Trail: 5 events logged
```

---

## 📱 **SCENARIO 2: Amina Orders 5 Dell Laptops from Tunde (Instagram)**

> *"I need 5 Dell XPS laptops for my startup — but I want a discount!"*

### 🔍 **Stage 1: Discovery & Negotiation**

**Real-World Action:**
- Amina sees Tunde's Instagram Reel: *"🔥 Dell XPS 15 — ₦250,000 each!"*
- DMs `@tundeelec`: *"I want 5. Discount for bulk?"*

**Bot (via Instagram):**
```
"Welcome, Amina! I dey verify you first. Send your phone number for SMS backup."
```

**Amina:**
```
+2348031234567
```

**OTP Flow (same as WhatsApp):**
- Bot sends 8-char OTP: `M3@Q8#R1` via Instagram DM
- Amina enters → ✅ Verified

**Negotiation (Vendor Dashboard):**
```typescript
// Tunde receives notification
toast.success(
  "New order from +234***4567",
  {
    description: "Instagram DM: 5 Dell XPS",
    action: {
      label: "View",
      onClick: () => router.push("/vendor/negotiation/order_def456")
    }
  }
)
```

**Tunde opens Negotiation View → types:**
```
5 units: ₦240,000 each = ₦1,200,000 total. Free delivery!
```

**Bot relays to Amina (Instagram DM):**
```
"Tunde says: 5 Dell XPS @ ₦240,000 each = ₦1,200,000. Free delivery."
```

**Amina:**
```
Can you do ₦1,150,000 for everything?
```

**Tunde clicks "Confirm Price" button:**
```typescript
// Quick Action in negotiation chat
await sendMessage({
  order_id: "order_def456",
  quick_action: "confirm_price",
  custom_amount: 1150000
})

// Bot sends via Instagram
"✅ Final: ₦1,150,000 for 5 Dell XPS. Free delivery. Ref: TG-9902."
```

---

### 🔐 **Stage 2: High-Value Escalation (₦1,150,000 > ₦1M Threshold)**

**System Auto-Creates Escalation:**
```typescript
// After receipt upload, system checks amount
if (order.total_amount >= 1000000) {
  await DynamoDB.putItem({
    TableName: "TrustGuard-Escalations",
    Item: {
      escalation_id: `esc_${Date.now()}`,
      order_id: order_id,
      vendor_id: vendor_id,
      ceo_id: ceo_id,
      reason: "HIGH_VALUE_TRANSACTION",
      amount: 1150000,
      status: "PENDING_CEO_APPROVAL",
      created_at: Math.floor(Date.now() / 1000)
    }
  })
  
  // Send SNS notification to CEO
  await sns.publish({
    TopicArn: `arn:aws:sns:us-east-1:123456789:TrustGuard-CEOAlerts-${ceo_id}`,
    Message: `High-Value Alert: ₦1,150,000 requires your approval (Order #${order_id})`
  })
}
```

**Tunde (CEO) receives email + SMS:**
```
Subject: 🚨 High-Value Escalation: ₦1,150,000

Order #def456
Buyer: +234***4567 (Amina)
Vendor: Tunde Electronics (YOU)
Amount: ₦1,150,000
Items: 5 Dell XPS Laptops

Click to review: https://trustguard.ng/ceo/escalations/esc_1732370600
```

**CEO Dashboard (Escalation Modal):**
```
High-Value Transaction Review
━━━━━━━━━━━━━━━━━━━━━━━━
Order ID: #def456
Buyer: +234***4567 (Amina)
Vendor: Tunde Electronics (YOU)
Amount: ₦1,150,000

Receipt Preview: [S3 image]

Textract Insights:
  ✅ Extracted amount: ₦1,150,000 (100% match)
  ✅ Vendor name: "Tunde Electronics" (match)
  ✅ Timestamp: 1h ago (valid)

Vendor Notes: "Bulk discount applied - 5 Dell XPS laptops"

[🟢 Approve] [🔴 Reject]
```

**Tunde clicks "Approve" → OTP Re-Auth Modal:**
```
┌─────────────────────────────────────┐
│  🛡️  Verify Your Identity          │
│                                     │
│  This action requires re-auth for   │
│  security.                          │
│                                     │
│  Action: Approve ₦1,150,000 order   │
│                                     │
│  Enter 6-Character CEO OTP:         │
│  ┌────────┐                        │
│  │ 7#9@2! │                        │
│  └────────┘                        │
│                                     │
│  [Resend OTP]  [Verify]            │
└─────────────────────────────────────┘
```

**Tunde enters OTP `7#9@2!` → Verified:**
```typescript
// Backend processes CEO approval
await DynamoDB.updateItem({
  TableName: "TrustGuard-Escalations",
  Key: { escalation_id },
  UpdateExpression: "SET #status = :status, ceo_approved_at = :timestamp",
  ExpressionAttributeValues: {
    ":status": "CEO_APPROVED",
    ":timestamp": Math.floor(Date.now() / 1000)
  }
})

await DynamoDB.updateItem({
  TableName: "TrustGuard-Orders",
  Key: { order_id },
  UpdateExpression: "SET #status = :status",
  ExpressionAttributeValues: { ":status": "CEO_APPROVED" }
})

// Log immutable audit
await logAudit({
  action: "ESCALATION_APPROVED",
  actor_id: ceo_id,
  ceo_id: ceo_id,
  details: { order_id, amount: 1150000, otp_verified: true }
})

// Notify buyer
await sendInstagramMessage({
  to: "aminatunde",
  text: "✅ Payment verified! CEO approved. Delivery starts tomorrow."
})
```

**Audit Log Entry:**
```json
{
  "action": "ESCALATION_APPROVED",
  "actor_id": "tunde_elec",
  "ceo_id": "tunde_elec",
  "timestamp": 1732380200,
  "details": {
    "order_id": "order_def456",
    "amount": 1150000,
    "escalation_reason": "HIGH_VALUE_TRANSACTION",
    "otp_verified": true,
    "vendor_id": "tunde_elec"
  }
}
```

---

## 👑 **SCENARIO 3: CEO Post-Registration Flows**

### 🔗 **Flow 1: Meta Account Connection (WhatsApp + Instagram)**

**Ada (CEO) logs in → Dashboard shows:**
```
┌────────────────────────────────────────────┐
│  Welcome, Ada! Complete your setup:        │
│                                            │
│  ⚠️ Connect your business accounts         │
│                                            │
│  [📱 Connect WhatsApp Business]            │
│  [📸 Connect Instagram Business]           │
└────────────────────────────────────────────┘
```

**Ada clicks "Connect WhatsApp":**
```typescript
// Frontend redirects to Meta OAuth
const oauthUrl = `https://www.facebook.com/v19.0/dialog/oauth?` +
  `client_id=${process.env.NEXT_PUBLIC_META_APP_ID}&` +
  `redirect_uri=${encodeURIComponent('https://trustguard.ng/ceo/oauth/callback')}&` +
  `scope=whatsapp_business_messaging&` +
  `state=${ceo_id}`

window.location.href = oauthUrl
```

**Ada logs in with Facebook (ada.ogunleye) → Grants permission:**
```
┌─────────────────────────────────────────┐
│  Ada's Fashion wants to:                │
│  • Send and receive messages on your    │
│    behalf via WhatsApp Business         │
│  • Access your WhatsApp Business        │
│    Account info                         │
│                                         │
│  [Continue as Ada Ogunleye] [Cancel]   │
└─────────────────────────────────────────┘
```

**Meta redirects to callback:**
```
https://trustguard.ng/ceo/oauth/callback?code=ABC123&state=ada_fashion
```

**Backend processes:**
```typescript
// Exchange code for long-lived token
const tokenResponse = await axios.get(
  `https://graph.facebook.com/v19.0/oauth/access_token?` +
  `client_id=${META_APP_ID}&` +
  `client_secret=${META_APP_SECRET}&` +
  `code=${code}&` +
  `redirect_uri=https://trustguard.ng/ceo/oauth/callback`
)

const { access_token, expires_in } = tokenResponse.data

// Store in AWS Secrets Manager (encrypted)
await secretsManager.putSecretValue({
  SecretId: `/ceo/${ceo_id}/meta`,
  SecretString: JSON.stringify({
    whatsapp_token: access_token,
    phone_number_id: "1234567890",
    expires_at: Date.now() + (expires_in * 1000),
    updated_at: Date.now()
  })
})

// Map phone_number_id to ceo_id in DynamoDB
await DynamoDB.putItem({
  TableName: "TrustGuard-CEOMapping",
  Item: {
    phone_number_id: "1234567890",
    ceo_id: ceo_id,
    platform: "whatsapp",
    connected_at: Math.floor(Date.now() / 1000)
  }
})

// Log audit
await logAudit({
  action: "META_ACCOUNT_CONNECTED",
  actor_id: ceo_id,
  ceo_id: ceo_id,
  details: { platform: "whatsapp", phone_masked: "+234***4567" }
})
```

**Dashboard updates:**
```
✅ WhatsApp Connected: +234***4567
   Phone ID: 1234567890
   Last synced: Just now
   [🔄 Reconnect] [❌ Disconnect]
```

---

### 🤖 **Flow 2: Chatbot Customization**

**Ada clicks "Settings" → "Customize Chatbot":**
```
┌────────────────────────────────────────────────┐
│  Chatbot Settings                              │
│                                                │
│  Greeting Message:                             │
│  ┌────────────────────────────────────────┐   │
│  │ Welcome to Ada's Fashion! How can I    │   │
│  │ help you today? 😊                      │   │
│  └────────────────────────────────────────┘   │
│                                                │
│  Tone & Language:                              │
│  ◉ Professional                                │
│  ○ Friendly                                    │
│  ○ Pidgin-English Friendly                     │
│                                                │
│  Fallback Message (when bot doesn't understand):
│  ┌────────────────────────────────────────┐   │
│  │ I no sabi dis question — Ada go reply  │   │
│  │ you soon!                               │   │
│  └────────────────────────────────────────┘   │
│                                                │
│  Business Hours:                               │
│  Mon-Sat: 9:00 AM – 6:00 PM WAT               │
│  [Edit Hours]                                  │
│                                                │
│  [Preview Bot] [Save Changes]                 │
└────────────────────────────────────────────────┘
```

**Ada clicks "Preview Bot" → Live Simulation:**
```
┌────────────────────────────────────────────┐
│  Bot Preview                               │
│                                            │
│  👤 You: hi                                │
│  🤖 Bot: Welcome to Ada's Fashion! How    │
│         can I help you today? 😊          │
│                                            │
│  👤 You: how much ankara dress            │
│  🤖 Bot: I no sabi dis question — Ada go  │
│         reply you soon!                    │
│                                            │
│  [Reset] [Close Preview]                  │
└────────────────────────────────────────────┘
```

**Ada selects "Pidgin-English Friendly" → Preview updates:**
```
│  👤 You: hi                                │
│  🤖 Bot: How you dey? Wetin you need?     │
```

**Ada clicks "Save Changes":**
```typescript
// Frontend validates input (XSS protection)
const sanitizedGreeting = DOMPurify.sanitize(greeting)

// API call
await api.put("/ceo/chatbot/settings", {
  greeting: sanitizedGreeting,
  tone: "pidgin-friendly",
  fallback: "I no sabi dis question — Ada go reply you soon!",
  business_hours: {
    days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    open: "09:00",
    close: "18:00",
    timezone: "Africa/Lagos"
  }
})

// Backend stores in DynamoDB
await DynamoDB.updateItem({
  TableName: "TrustGuard-Users",
  Key: { user_id: ceo_id },
  UpdateExpression: "SET chat_config = :config",
  ExpressionAttributeValues: {
    ":config": {
      greeting: sanitizedGreeting,
      tone: "pidgin-friendly",
      fallback: "I no sabi dis question...",
      business_hours: {...}
    }
  }
})

// Log audit
await logAudit({
  action: "CHATBOT_CONFIG_UPDATED",
  actor_id: ceo_id,
  ceo_id: ceo_id
})
```

---

### 👤 **Flow 3: CEO Detail Change (Profile Management)**

**Ada clicks "Settings" → "Profile":**
```
┌────────────────────────────────────────────┐
│  Profile Settings                          │
│                                            │
│  Full Name:                                │
│  ┌────────────────┐                       │
│  │ Ada Ogunleye   │                       │
│  └────────────────┘                       │
│                                            │
│  Phone Number:                             │
│  ┌────────────────┐                       │
│  │ +2348031234567 │ [🔒 OTP Required]    │
│  └────────────────┘                       │
│                                            │
│  Email:                                    │
│  ┌────────────────────────────────┐       │
│  │ ada@adasfashion.ng              │      │
│  └────────────────────────────────┘       │
│                                            │
│  Business Name:                            │
│  ┌────────────────────┐                   │
│  │ Ada's Fashion      │                   │
│  └────────────────────┘                   │
│                                            │
│  [Save Changes]                            │
└────────────────────────────────────────────┘
```

**Ada changes phone to `+2348099999999` → clicks "Save":**

**OTP Re-Auth Modal appears:**
```
┌─────────────────────────────────────┐
│  🛡️  Verify Your Identity          │
│                                     │
│  Sensitive changes require OTP.     │
│                                     │
│  Action: Update phone number        │
│  From: +234***4567                  │
│  To: +234***9999                    │
│                                     │
│  Enter 6-Character OTP:             │
│  (sent to OLD number)               │
│  ┌────────┐                        │
│  │ 7#9@2! │                        │
│  └────────┘                        │
│                                     │
│  [Resend OTP]  [Verify]            │
└─────────────────────────────────────┘
```

**Ada enters OTP → Backend processes:**
```typescript
// Verify OTP against old phone number
const otpValid = await verifyOTP(old_phone, otp_input)

if (otpValid) {
  // Update phone in Users table
  await DynamoDB.updateItem({
    TableName: "TrustGuard-Users",
    Key: { user_id: ceo_id },
    UpdateExpression: "SET phone = :new_phone, updated_at = :timestamp",
    ExpressionAttributeValues: {
      ":new_phone": "+2348099999999",
      ":timestamp": Math.floor(Date.now() / 1000)
    }
  })
  
  // Invalidate old JWT (force re-login)
  await blacklistToken(current_jwt)
  
  // Send verification to NEW phone
  await sendSMS({
    to: "+2348099999999",
    message: "Your phone number was updated on TrustGuard. If this wasn't you, contact support immediately."
  })
  
  // Log audit
  await logAudit({
    action: "PROFILE_UPDATED",
    actor_id: ceo_id,
    ceo_id: ceo_id,
    details: {
      field: "phone",
      old_value_masked: "+234***4567",
      new_value_masked: "+234***9999",
      otp_verified: true
    }
  })
  
  // Force logout
  res.status(200).json({
    status: "success",
    message: "Phone updated. Please login again.",
    force_logout: true
  })
}
```

**Audit Log Entry:**
```json
{
  "action": "PROFILE_UPDATED",
  "actor_id": "ada_fashion",
  "ceo_id": "ada_fashion",
  "timestamp": 1732383800,
  "details": {
    "field": "phone",
    "old_value_masked": "+234***4567",
    "new_value_masked": "+234***9999",
    "otp_verified": true,
    "ip_address": "105.112.34.56",
    "user_agent": "Mozilla/5.0..."
  }
}
```

---

## 🛡️ **Zero Trust Principles in Every Flow**

| Flow | Zero Trust Control | Implementation |
|------|-------------------|----------------|
| **Buyer OTP** | Never trust, always verify | 8-char OTP, PBKDF2-hashed, 5-min TTL, single-use |
| **Receipt Upload** | Assume breach | SSE-KMS encryption, checksum validation, S3 presigned URLs |
| **Vendor Approval** | Least privilege | GSI `ByVendorAndCEO` scopes queries to `vendor_id` + `ceo_id` |
| **CEO Escalation** | Explicit verification | OTP re-auth for high-value (>₦1M), immutable audit logs |
| **Meta OAuth** | Secure token storage | Long-lived tokens in Secrets Manager, rotated on expiry |
| **Chatbot Config** | Input validation | DOMPurify sanitization, XSS protection |
| **Profile Changes** | Re-authentication | OTP sent to OLD phone/email before update, JWT invalidated |

---

## 📊 **System-Wide Audit Trail**

**Example: Full lifecycle audit for Order #abc123**

```sql
SELECT * FROM "TrustGuard-AuditLogs" 
WHERE details.order_id = 'order_abc123' 
ORDER BY timestamp ASC
```

**Results:**
```json
[
  {
    "action": "BUYER_REGISTERED",
    "actor_id": "wa_2348031234567",
    "timestamp": 1732370400,
    "details": { "platform": "whatsapp", "masked_phone": "+234***4567" }
  },
  {
    "action": "OTP_VERIFY_SUCCESS",
    "actor_id": "wa_2348031234567",
    "timestamp": 1732370460,
    "details": { "attempts": 1 }
  },
  {
    "action": "RECEIPT_UPLOADED",
    "actor_id": "wa_2348031234567",
    "timestamp": 1732370520,
    "details": { "order_id": "order_abc123", "amount": 12500, "checksum": "sha256:abcd..." }
  },
  {
    "action": "RECEIPT_APPROVED",
    "actor_id": "ceo_ada_fashion",
    "timestamp": 1732377600,
    "details": { "order_id": "order_abc123", "amount": 12500 }
  },
  {
    "action": "ORDER_CONFIRMED",
    "actor_id": "wa_2348031234567",
    "timestamp": 1732377660,
    "details": { "order_id": "order_abc123", "delivery_address": "123 Lagos St, Ikeja" }
  }
]
```

**Forensic Use Case:**
- If Chinedu disputes delivery, CEO can export this audit trail (PII-redacted).
- Each action is immutable (write-only DynamoDB table).
- Cryptographic checksums prevent tampering.

---

## 🎯 **Dissertation Takeaways**

1. **Sessionless Authentication**: No persistent sessions → OTP for every sensitive action
2. **Multi-Tenancy**: Each CEO (`ceo_id`) operates isolated data — no cross-contamination
3. **Least Privilege**: Vendors see only their orders (GSI scoped by `vendor_id` + `ceo_id`)
4. **Immutable Audit**: Write-only logs with cryptographic integrity
5. **Platform Agnostic**: WhatsApp + Instagram unified via Meta OAuth tokens
6. **Real-World Ready**: Pidgin support, Nigerian phone formats, local payment flows

---

**Document Status:** Comprehensive narrative ready for dissertation Chapter 4 (Implementation)  
**Last Updated:** 2025-11-23  
**Author:** TrustGuard Engineering Team
