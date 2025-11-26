#!/usr/bin/env python3
"""
Seed Meta API credentials to AWS Secrets Manager.

Usage:
    python seed_meta_secrets.py --whatsapp-token <TOKEN> --whatsapp-phone-id <PHONE_ID>
    python seed_meta_secrets.py --instagram-token <TOKEN> --instagram-page-id <PAGE_ID>
    python seed_meta_secrets.py --all --whatsapp-token <TOKEN> --whatsapp-phone-id <PHONE_ID> \
                                      --instagram-token <TOKEN> --instagram-page-id <PAGE_ID>
"""

import boto3
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Configuration
REGION = 'us-east-1'
SECRET_NAME = '/TrustGuard/dev/meta-TrustGuard-Dev'

def get_current_secrets():
    """Retrieve current secrets from Secrets Manager."""
    client = boto3.client('secretsmanager', region_name=REGION)
    try:
        response = client.get_secret_value(SecretId=SECRET_NAME)
        return json.loads(response['SecretString'])
    except client.exceptions.ResourceNotFoundException:
        print(f"⚠️  Secret {SECRET_NAME} not found. Will create new secret.")
        return {}
    except Exception as e:
        print(f"❌ Error retrieving secrets: {e}")
        return {}

def update_secrets(whatsapp_token=None, whatsapp_phone_id=None, 
                   instagram_token=None, instagram_page_id=None):
    """Update Meta API secrets in Secrets Manager."""
    
    client = boto3.client('secretsmanager', region_name=REGION)
    
    # Get current secrets
    current_secrets = get_current_secrets()
    print(f"\n📋 Current secrets: {list(current_secrets.keys())}")
    
    # Update with new values
    updated = False
    
    if whatsapp_token:
        current_secrets['whatsapp_access_token'] = whatsapp_token
        updated = True
        print(f"✓ WhatsApp Access Token: {whatsapp_token[:20]}...{whatsapp_token[-10:]}")
    
    if whatsapp_phone_id:
        current_secrets['whatsapp_phone_number_id'] = whatsapp_phone_id
        updated = True
        print(f"✓ WhatsApp Phone Number ID: {whatsapp_phone_id}")
    
    if instagram_token:
        current_secrets['instagram_access_token'] = instagram_token
        updated = True
        print(f"✓ Instagram Access Token: {instagram_token[:20]}...{instagram_token[-10:]}")
    
    if instagram_page_id:
        current_secrets['instagram_page_id'] = instagram_page_id
        updated = True
        print(f"✓ Instagram Page ID: {instagram_page_id}")
    
    if not updated:
        print("❌ No secrets provided. Use --help for usage.")
        return False
    
    # Add metadata
    current_secrets['last_updated'] = datetime.utcnow().isoformat()
    current_secrets['environment'] = 'dev'
    
    # Update Secrets Manager
    try:
        client.put_secret_value(
            SecretId=SECRET_NAME,
            SecretString=json.dumps(current_secrets, indent=2)
        )
        print(f"\n✅ Successfully updated secrets in {SECRET_NAME}")
        print(f"\n📊 Complete secret structure:")
        # Mask tokens when displaying
        display_secrets = current_secrets.copy()
        for key in ['whatsapp_access_token', 'instagram_access_token']:
            if key in display_secrets:
                token = display_secrets[key]
                display_secrets[key] = f"{token[:15]}...{token[-8:]}"
        print(json.dumps(display_secrets, indent=2))
        return True
        
    except Exception as e:
        print(f"❌ Error updating secrets: {e}")
        return False

def verify_webhook_configuration():
    """Verify webhook configuration."""
    print("\n" + "="*70)
    print("🔍 WEBHOOK VERIFICATION")
    print("="*70)
    
    # Test WhatsApp webhook
    print("\n📱 Testing WhatsApp Webhook...")
    import requests
    try:
        response = requests.get(
            "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_trusgu@rd_25",
                "hub.challenge": "12345"
            },
            timeout=10
        )
        if response.status_code == 200 and response.text == "12345":
            print("   ✅ WhatsApp webhook verification PASSED")
        else:
            print(f"   ⚠️  WhatsApp webhook returned: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ WhatsApp webhook test failed: {str(e)[:100]}")
    
    # Test Instagram webhook
    print("\n📸 Testing Instagram Webhook...")
    try:
        response = requests.get(
            "https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod/integrations/webhook/instagram",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_trusgu@rd_25",
                "hub.challenge": "54321"
            },
            timeout=10
        )
        if response.status_code == 200 and response.text == "54321":
            print("   ✅ Instagram webhook verification PASSED")
        else:
            print(f"   ⚠️  Instagram webhook returned: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Instagram webhook test failed: {str(e)[:100]}")

def main():
    parser = argparse.ArgumentParser(
        description="Seed Meta API credentials to AWS Secrets Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add WhatsApp credentials only
  python seed_meta_secrets.py --whatsapp-token EAAMxxxxx --whatsapp-phone-id 123456789

  # Add Instagram credentials only
  python seed_meta_secrets.py --instagram-token EAAMxxxxx --instagram-page-id 987654321

  # Add both at once
  python seed_meta_secrets.py --all \\
      --whatsapp-token EAAMxxxxx --whatsapp-phone-id 123456789 \\
      --instagram-token EAAMxxxxx --instagram-page-id 987654321
  
  # Verify webhooks only
  python seed_meta_secrets.py --verify
        """
    )
    
    parser.add_argument('--whatsapp-token', help='WhatsApp Business API access token')
    parser.add_argument('--whatsapp-phone-id', help='WhatsApp Phone Number ID')
    parser.add_argument('--instagram-token', help='Instagram/Messenger Page access token')
    parser.add_argument('--instagram-page-id', help='Instagram Page ID')
    parser.add_argument('--all', action='store_true', help='Update all credentials at once')
    parser.add_argument('--verify', action='store_true', help='Verify webhook configuration only')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🔐 TrustGuard - Meta API Secrets Manager")
    print("="*70)
    print(f"Region: {REGION}")
    print(f"Secret: {SECRET_NAME}")
    print("="*70)
    
    if args.verify:
        verify_webhook_configuration()
        return
    
    # Validate inputs
    has_whatsapp = args.whatsapp_token or args.whatsapp_phone_id
    has_instagram = args.instagram_token or args.instagram_page_id
    
    if not has_whatsapp and not has_instagram:
        print("\n❌ No credentials provided. Use --help for usage.")
        parser.print_help()
        return
    
    # Update secrets
    success = update_secrets(
        whatsapp_token=args.whatsapp_token,
        whatsapp_phone_id=args.whatsapp_phone_id,
        instagram_token=args.instagram_token,
        instagram_page_id=args.instagram_page_id
    )
    
    if success:
        print("\n" + "="*70)
        print("✅ SECRETS SUCCESSFULLY UPDATED")
        print("="*70)
        print("\n📋 Next Steps:")
        print("1. Go to Meta App Dashboard and configure webhooks")
        print("2. Use the callback URLs from WEBHOOK_URLS.txt")
        print("3. Verify webhooks using: python seed_meta_secrets.py --verify")
        print("4. Test end-to-end buyer registration via WhatsApp/Instagram")
        
        # Auto-verify after update
        if input("\nRun webhook verification now? (y/n): ").lower() == 'y':
            verify_webhook_configuration()

if __name__ == "__main__":
    main()
