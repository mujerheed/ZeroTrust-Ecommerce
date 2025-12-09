# Facebook Business Page Requirement for TrustGuard OAuth

## Why Do CEOs Need a Facebook Business Page?

### For WhatsApp Business API
- **Requirement**: WhatsApp Business API requires a **Facebook Business Manager** account
- **Connection**: Your WhatsApp Business Account must be linked to a Facebook Business Page
- **Reason**: Meta uses Facebook Business Manager to manage WhatsApp Business API access

### For Instagram Messaging API
- **Requirement**: Instagram Professional Account must be connected to a Facebook Business Page
- **Connection**: Instagram messaging features are managed through Facebook
- **Reason**: Meta's unified platform requires Facebook Page as the central hub

---

## Setup Steps for CEOs

### Step 1: Create Facebook Business Page (If Not Already Done)

1. Go to [facebook.com/pages/create](https://www.facebook.com/pages/create)
2. Choose **Business or Brand**
3. Fill in:
   - **Page Name**: Your business name (e.g., "Alice's Fashion Store")
   - **Category**: Choose relevant category (e.g., "Retail Company", "Clothing Store")
   - **Description**: Brief description of your business
4. Click **Create Page**

### Step 2: Set Up Facebook Business Manager

1. Go to [business.facebook.com](https://business.facebook.com)
2. Click **Create Account**
3. Enter:
   - Business name
   - Your name
   - Business email
4. Add your Facebook Page to Business Manager:
   - Go to **Business Settings** → **Pages**
   - Click **Add** → **Add a Page**
   - Select your page

### Step 3: Connect WhatsApp Business Account

1. In Business Manager, go to **WhatsApp Accounts**
2. Click **Add** → **Create a WhatsApp Business Account**
3. Follow the setup wizard:
   - Verify your business phone number
   - Link to your Facebook Page
   - Set up business profile

### Step 4: Connect Instagram Professional Account

1. Convert Instagram to Professional Account:
   - Open Instagram app
   - Go to **Settings** → **Account** → **Switch to Professional Account**
   - Choose **Business** or **Creator**
2. Connect to Facebook Page:
   - In Instagram settings, go to **Page**
   - Select your Facebook Business Page
   - Confirm connection

### Step 5: Connect to TrustGuard

1. Log in to TrustGuard CEO Dashboard
2. Go to **Integrations** page
3. Click **Connect WhatsApp Business** or **Connect Instagram**
4. Grant permissions when prompted
5. You'll be redirected to success page after connection

---

## Common Issues & Solutions

### Issue 1: "You don't have a Facebook Page"
**Solution**: Create a Facebook Business Page first (Step 1 above)

### Issue 2: "WhatsApp number not verified"
**Solution**: 
- Go to Meta Business Manager → WhatsApp Accounts
- Verify your business phone number via SMS/call
- Wait 24 hours for verification

### Issue 3: "Instagram account not eligible"
**Solution**:
- Make sure Instagram is a **Professional Account** (not personal)
- Must have at least 100 followers (Meta requirement)
- Account must be at least 30 days old

### Issue 4: "Permission denied during OAuth"
**Solution**:
- Make sure you grant ALL requested permissions
- Check that you're logged into the correct Facebook account
- Try again from TrustGuard integrations page

---

## What Permissions Does TrustGuard Need?

### WhatsApp Business API
- ✅ `whatsapp_business_management` - Manage WhatsApp Business Account
- ✅ `whatsapp_business_messaging` - Send and receive messages
- ✅ `business_management` - Access Business Manager

### Instagram Messaging API
- ✅ `instagram_basic` - Access basic Instagram data
- ✅ `instagram_manage_messages` - Send and receive Instagram DMs
- ✅ `pages_messaging` - Manage page messages

---

## Security & Privacy

### What TrustGuard DOES:
- ✅ Store access tokens securely in AWS Secrets Manager
- ✅ Use tokens only to send/receive messages on your behalf
- ✅ Encrypt all data at rest and in transit

### What TrustGuard DOES NOT:
- ❌ Post to your Facebook Page
- ❌ Access your personal Facebook data
- ❌ Share your tokens with third parties
- ❌ Use your account for anything other than messaging

---

## Token Expiry & Refresh

- **Token Lifetime**: 60 days (Meta default)
- **Auto-Refresh**: TrustGuard automatically refreshes tokens before expiry
- **Notification**: You'll receive an alert 7 days before token expiry
- **Manual Refresh**: You can manually refresh from Integrations page

---

## Testing Your Connection

After connecting, test the integration:

1. **WhatsApp Test**:
   - Send a message to your WhatsApp Business number
   - Check TrustGuard dashboard for incoming message
   - Reply from vendor dashboard

2. **Instagram Test**:
   - Send a DM to your Instagram business account
   - Check TrustGuard dashboard for incoming message
   - Reply from vendor dashboard

---

## Troubleshooting

### Connection shows "Connected" but messages not received?

1. **Check Webhook Configuration**:
   - Go to Meta App Dashboard
   - Verify webhook URL: `https://your-backend-url/webhook`
   - Ensure webhook is subscribed to `messages` field

2. **Check Token Status**:
   - Go to TrustGuard Integrations page
   - Look for token expiry date
   - Click "Refresh Token" if expired

3. **Check Meta App Status**:
   - Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
   - Ensure app is in "Live" mode (not Development)
   - Check app review status

---

## Need Help?

- **Meta Business Help**: [business.facebook.com/help](https://business.facebook.com/help)
- **WhatsApp API Docs**: [developers.facebook.com/docs/whatsapp](https://developers.facebook.com/docs/whatsapp)
- **Instagram API Docs**: [developers.facebook.com/docs/instagram](https://developers.facebook.com/docs/instagram)
- **TrustGuard Support**: Contact your system administrator

---

**Last Updated**: December 8, 2025
