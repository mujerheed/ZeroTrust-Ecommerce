#!/bin/bash

# 🚀 TrustGuard Meta API Quick Setup Script
# Run this after completing Meta Developer Console setup

set -e  # Exit on error

echo "=============================================="
echo "  TrustGuard Meta API Setup"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env 2>/dev/null || touch .env
fi

echo -e "${BLUE}📝 Please provide your Meta API credentials:${NC}"
echo ""

# Function to prompt for input
prompt_input() {
    local var_name=$1
    local prompt_text=$2
    local is_secret=${3:-false}
    
    # Check if already set in .env
    if grep -q "^${var_name}=" .env 2>/dev/null; then
        current_value=$(grep "^${var_name}=" .env | cut -d'=' -f2-)
        if [ -n "$current_value" ] && [ "$current_value" != '""' ]; then
            echo -e "${GREEN}✓${NC} $var_name already set"
            return
        fi
    fi
    
    if [ "$is_secret" = true ]; then
        read -sp "$prompt_text: " value
        echo ""
    else
        read -p "$prompt_text: " value
    fi
    
    # Remove existing line if present
    sed -i "/^${var_name}=/d" .env
    
    # Add new value
    echo "${var_name}=${value}" >> .env
}

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Meta App Credentials${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

prompt_input "META_APP_ID" "Meta App ID"
prompt_input "META_APP_SECRET" "Meta App Secret (will be hidden)" true
prompt_input "META_WEBHOOK_VERIFY_TOKEN" "Webhook Verify Token (create a random string)"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  WhatsApp Business API${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

prompt_input "WHATSAPP_PHONE_NUMBER_ID" "WhatsApp Phone Number ID"
prompt_input "WHATSAPP_BUSINESS_ACCOUNT_ID" "WhatsApp Business Account ID"
prompt_input "WHATSAPP_ACCESS_TOKEN" "WhatsApp Access Token (System User token)" true

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Instagram Messaging API${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

prompt_input "INSTAGRAM_ACCOUNT_ID" "Instagram Account ID"
prompt_input "INSTAGRAM_PAGE_ID" "Instagram/Facebook Page ID"
prompt_input "INSTAGRAM_ACCESS_TOKEN" "Instagram Access Token (can be same as WhatsApp)" true

echo ""
echo -e "${GREEN}✅ Configuration saved to .env${NC}"
echo ""

# Test Meta API connection
echo -e "${BLUE}🧪 Testing Meta API connection...${NC}"
echo ""

python3 << 'PYTHON_TEST'
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def test_api(name, url, token):
    """Test API endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ {name}: Connected successfully")
            return True
        else:
            print(f"❌ {name}: Failed - Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False

# Test WhatsApp API
whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
whatsapp_token = os.getenv('WHATSAPP_ACCESS_TOKEN')

if whatsapp_phone_id and whatsapp_token:
    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_id}"
    test_api("WhatsApp API", url, whatsapp_token)
else:
    print("⚠️  WhatsApp credentials not configured")

print()

# Test Instagram API
instagram_account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

if instagram_account_id and instagram_token:
    url = f"https://graph.facebook.com/v18.0/{instagram_account_id}"
    test_api("Instagram API", url, instagram_token)
else:
    print("⚠️  Instagram credentials not configured")

PYTHON_TEST

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Next Steps${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Start ngrok tunnel:"
echo -e "   ${BLUE}ngrok http 8000${NC}"
echo ""
echo "2. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)"
echo ""
echo "3. Configure webhooks in Meta Dashboard:"
echo "   WhatsApp: https://YOUR_NGROK_URL/integrations/webhook/whatsapp"
echo "   Instagram: https://YOUR_NGROK_URL/integrations/webhook/instagram"
echo ""
echo "4. Restart backend with new credentials:"
echo -e "   ${BLUE}cd backend && uvicorn app:app --reload${NC}"
echo ""
echo "5. Send test message to your WhatsApp/Instagram business account"
echo ""
echo -e "${GREEN}✨ Setup complete! Check META_API_SETUP_GUIDE.md for detailed instructions.${NC}"
echo ""
