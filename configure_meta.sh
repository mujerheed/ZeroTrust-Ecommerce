#!/bin/bash

# 🔐 TrustGuard Meta API Credentials Setup
# This script will securely add your Meta API credentials to .env

set -e

echo "=============================================="
echo "  TrustGuard Meta API Credentials Setup"
echo "=============================================="
echo ""
echo "This script will help you configure Meta API credentials."
echo "Your credentials will be saved to backend/.env file."
echo ""
echo "Press Ctrl+C at any time to cancel."
echo ""

cd "$(dirname "$0")/backend"

# Ensure .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    touch .env
fi

# Function to add or update env variable
update_env() {
    local key=$1
    local value=$2
    
    # Remove existing line
    sed -i "/^${key}=/d" .env
    
    # Add new value
    echo "${key}=${value}" >> .env
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Step 1: Meta App Credentials"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Get these from: https://developers.facebook.com/apps"
echo "→ Your App → Settings → Basic"
echo ""

# Check if already set
if grep -q "^META_APP_ID=" .env 2>/dev/null; then
    current=$(grep "^META_APP_ID=" .env | cut -d'=' -f2)
    if [ -n "$current" ]; then
        echo "✓ META_APP_ID already set: ${current:0:10}..."
        read -p "Update? (y/N): " update
        if [ "$update" != "y" ]; then
            META_APP_ID=$current
        fi
    fi
fi

if [ -z "$META_APP_ID" ]; then
    read -p "Enter META_APP_ID: " META_APP_ID
    update_env "META_APP_ID" "$META_APP_ID"
fi

# Meta App Secret
if grep -q "^META_APP_SECRET=" .env 2>/dev/null; then
    current=$(grep "^META_APP_SECRET=" .env | cut -d'=' -f2)
    if [ -n "$current" ]; then
        echo "✓ META_APP_SECRET already set: ${current:0:10}..."
        read -p "Update? (y/N): " update
        if [ "$update" != "y" ]; then
            META_APP_SECRET=$current
        fi
    fi
fi

if [ -z "$META_APP_SECRET" ]; then
    read -sp "Enter META_APP_SECRET (hidden): " META_APP_SECRET
    echo ""
    update_env "META_APP_SECRET" "$META_APP_SECRET"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Step 2: Webhook Verify Token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This is a random string you create for webhook security."
echo ""

if grep -q "^META_WEBHOOK_VERIFY_TOKEN=" .env 2>/dev/null; then
    current=$(grep "^META_WEBHOOK_VERIFY_TOKEN=" .env | cut -d'=' -f2)
    if [ -n "$current" ]; then
        echo "✓ META_WEBHOOK_VERIFY_TOKEN already set"
        read -p "Update? (y/N): " update
        if [ "$update" != "y" ]; then
            META_WEBHOOK_VERIFY_TOKEN=$current
        fi
    fi
fi

if [ -z "$META_WEBHOOK_VERIFY_TOKEN" ]; then
    # Generate random token
    suggested=$(openssl rand -hex 16 2>/dev/null || echo "trustguard_verify_$(date +%s)")
    echo "Suggested token: $suggested"
    read -p "Press Enter to use suggested, or type your own: " custom_token
    
    if [ -z "$custom_token" ]; then
        META_WEBHOOK_VERIFY_TOKEN=$suggested
    else
        META_WEBHOOK_VERIFY_TOKEN=$custom_token
    fi
    
    update_env "META_WEBHOOK_VERIFY_TOKEN" "$META_WEBHOOK_VERIFY_TOKEN"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Step 3: WhatsApp Business API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Get these from: https://developers.facebook.com/apps"
echo "→ Your App → WhatsApp → Getting Started"
echo ""
read -p "Do you have WhatsApp credentials? (y/N): " has_whatsapp

if [ "$has_whatsapp" = "y" ]; then
    read -p "Enter WHATSAPP_PHONE_NUMBER_ID: " WHATSAPP_PHONE_NUMBER_ID
    update_env "WHATSAPP_PHONE_NUMBER_ID" "$WHATSAPP_PHONE_NUMBER_ID"
    
    read -p "Enter WHATSAPP_BUSINESS_ACCOUNT_ID: " WHATSAPP_BUSINESS_ACCOUNT_ID
    update_env "WHATSAPP_BUSINESS_ACCOUNT_ID" "$WHATSAPP_BUSINESS_ACCOUNT_ID"
    
    read -sp "Enter WHATSAPP_ACCESS_TOKEN (hidden): " WHATSAPP_ACCESS_TOKEN
    echo ""
    update_env "WHATSAPP_ACCESS_TOKEN" "$WHATSAPP_ACCESS_TOKEN"
else
    echo "⚠️  Skipping WhatsApp configuration"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Step 4: Instagram Messaging API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Get these from: https://developers.facebook.com/apps"
echo "→ Your App → Instagram → Getting Started"
echo ""
read -p "Do you have Instagram credentials? (y/N): " has_instagram

if [ "$has_instagram" = "y" ]; then
    read -p "Enter INSTAGRAM_ACCOUNT_ID: " INSTAGRAM_ACCOUNT_ID
    update_env "INSTAGRAM_ACCOUNT_ID" "$INSTAGRAM_ACCOUNT_ID"
    
    read -p "Enter INSTAGRAM_PAGE_ID: " INSTAGRAM_PAGE_ID
    update_env "INSTAGRAM_PAGE_ID" "$INSTAGRAM_PAGE_ID"
    
    read -sp "Enter INSTAGRAM_ACCESS_TOKEN (hidden): " INSTAGRAM_ACCESS_TOKEN
    echo ""
    update_env "INSTAGRAM_ACCESS_TOKEN" "$INSTAGRAM_ACCESS_TOKEN"
else
    echo "⚠️  Skipping Instagram configuration"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Configuration Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Credentials saved to backend/.env"
echo ""
echo "Next steps:"
echo ""
echo "1. Test connection:"
echo "   python3 test_meta_api.py"
echo ""
echo "2. Start ngrok (for webhook testing):"
echo "   ngrok http 8000"
echo ""
echo "3. Configure webhooks in Meta Dashboard with ngrok URL"
echo ""
echo "4. Restart backend server:"
echo "   cd backend && uvicorn app:app --reload"
echo ""
