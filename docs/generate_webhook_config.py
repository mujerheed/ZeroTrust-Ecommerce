#!/usr/bin/env python3
"""
Generate Webhook Configuration from Environment Variables

This script reads your actual AWS deployment and environment configuration
to generate the correct webhook URLs for Meta App Dashboard.

Usage:
    python3 generate_webhook_config.py
"""

import os
import json
import subprocess
from pathlib import Path

def get_env_value(key, default=None):
    """Get value from .env file or environment"""
    env_file = Path(__file__).parent.parent / 'backend' / '.env'
    
    # Try environment variable first
    value = os.getenv(key)
    if value:
        return value
    
    # Try .env file
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    
    return default


def get_aws_api_url():
    """Get API Gateway URL from AWS CloudFormation stack"""
    try:
        stack_name = get_env_value('AWS_STACK_NAME', 'TrustGuard-Dev')
        region = get_env_value('AWS_REGION', 'us-east-1')
        
        result = subprocess.run(
            [
                'aws', 'cloudformation', 'describe-stacks',
                '--stack-name', stack_name,
                '--region', region,
                '--query', 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue',
                '--output', 'text'
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        print(f"⚠️  Could not fetch AWS API URL from stack '{stack_name}'")
        return None
    
    except Exception as e:
        print(f"⚠️  Error fetching AWS API URL: {e}")
        return None


def generate_config():
    """Generate webhook configuration"""
    
    print("🔍 Reading configuration from environment...\n")
    
    # Get configuration values
    meta_app_id = get_env_value('META_APP_ID', 'YOUR_META_APP_ID')
    meta_app_secret = get_env_value('META_APP_SECRET', 'YOUR_META_APP_SECRET')
    verify_token = get_env_value('META_WEBHOOK_VERIFY_TOKEN', 'trustguard_verify_2025')
    
    # Get base URL (try AWS first, then fallback to env)
    base_url = get_aws_api_url()
    
    if not base_url:
        # Fallback to environment variable
        base_url = get_env_value('OAUTH_CALLBACK_BASE_URL', 'http://localhost:8000')
        print(f"📍 Using base URL from .env: {base_url}")
    else:
        print(f"📍 Using AWS API Gateway URL: {base_url}")
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    # Generate webhook URLs
    whatsapp_webhook = f"{base_url}/integrations/webhook/whatsapp"
    instagram_webhook = f"{base_url}/integrations/webhook/instagram"
    
    # Determine environment
    is_production = 'amazonaws.com' in base_url
    environment = "AWS Lambda (Production)" if is_production else "Local Development"
    
    # Generate markdown documentation
    config_md = f"""# TrustGuard Webhook Configuration

**Generated:** {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}  
**Environment:** {environment}  
**Base URL:** `{base_url}`

---

## 📱 Meta App Configuration

### Your Meta App Details

| Setting | Value |
|---------|-------|
| **App ID** | `{meta_app_id}` |
| **App Secret** | `{meta_app_secret[:8]}...` (hidden) |
| **Verify Token** | `{verify_token}` |

---

## 🔗 Webhook URLs

### WhatsApp Business API

**Callback URL:**
```
{whatsapp_webhook}
```

**Verify Token:**
```
{verify_token}
```

**Subscribe to Fields:**
- ✅ `messages`
- ✅ `messaging_postbacks` (optional)

---

### Instagram Messaging API

**Callback URL:**
```
{instagram_webhook}
```

**Verify Token:**
```
{verify_token}
```

**Subscribe to Fields:**
- ✅ `messages`
- ✅ `messaging_postbacks` (optional)

---

## 🔧 Configuration Steps

### 1. Go to Meta App Dashboard
Visit: [developers.facebook.com/apps/{meta_app_id}](https://developers.facebook.com/apps/{meta_app_id}/webhooks/)

### 2. Configure WhatsApp Webhook
1. Find **WhatsApp** section
2. Click **Edit** → Callback URL
3. Paste: `{whatsapp_webhook}`
4. Verify Token: `{verify_token}`
5. Click **Verify and Save**
6. Subscribe to `messages` field

### 3. Configure Instagram Webhook
1. Find **Instagram** section
2. Click **Edit** → Callback URL
3. Paste: `{instagram_webhook}`
4. Verify Token: `{verify_token}`
5. Click **Verify and Save**
6. Subscribe to `messages` field

---

## ✅ Testing

### Test WhatsApp Webhook
```bash
curl -X POST {whatsapp_webhook} \\
  -H "Content-Type: application/json" \\
  -H "X-Hub-Signature-256: sha256=test" \\
  -d '{{"object":"whatsapp_business_account"}}'
```

### Test Instagram Webhook
```bash
curl -X POST {instagram_webhook} \\
  -H "Content-Type: application/json" \\
  -H "X-Hub-Signature-256: sha256=test" \\
  -d '{{"object":"instagram"}}'
```

---

## 📊 Environment Variables

Current configuration from `.env`:

```bash
META_APP_ID={meta_app_id}
META_APP_SECRET={meta_app_secret[:8]}...
META_WEBHOOK_VERIFY_TOKEN={verify_token}
OAUTH_CALLBACK_BASE_URL={get_env_value('OAUTH_CALLBACK_BASE_URL', 'http://localhost:8000')}
```

---

## 🔄 Update Configuration

To regenerate this file with latest values:

```bash
cd docs
python3 generate_webhook_config.py
```

---

**Auto-generated from environment variables**  
**Do not edit manually - run script to regenerate**
"""
    
    # Save to file
    output_file = Path(__file__).parent / 'WEBHOOK_CONFIG.md'
    with open(output_file, 'w') as f:
        f.write(config_md)
    
    print(f"\n✅ Configuration saved to: {output_file}")
    print(f"\n📋 Quick Copy-Paste:\n")
    print(f"WhatsApp Webhook URL:")
    print(f"  {whatsapp_webhook}\n")
    print(f"Instagram Webhook URL:")
    print(f"  {instagram_webhook}\n")
    print(f"Verify Token:")
    print(f"  {verify_token}\n")
    
    # Also output as JSON for programmatic use
    json_config = {
        "meta_app_id": meta_app_id,
        "verify_token": verify_token,
        "base_url": base_url,
        "webhooks": {
            "whatsapp": whatsapp_webhook,
            "instagram": instagram_webhook
        },
        "environment": environment
    }
    
    json_file = Path(__file__).parent / 'webhook_config.json'
    with open(json_file, 'w') as f:
        json.dump(json_config, f, indent=2)
    
    print(f"📄 JSON config saved to: {json_file}\n")


if __name__ == '__main__':
    generate_config()
