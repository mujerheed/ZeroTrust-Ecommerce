#!/usr/bin/env python3
"""
Test sending a WhatsApp message via Meta API.
"""

import requests
import json
import boto3

def get_whatsapp_credentials():
    """Get WhatsApp credentials from Secrets Manager."""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='/TrustGuard/dev/meta-TrustGuard-Dev')
    secrets = json.loads(response['SecretString'])
    return {
        'token': secrets.get('whatsapp_access_token'),
        'phone_id': secrets.get('whatsapp_phone_number_id')
    }

def send_test_message(to_number, message_text):
    """Send a test WhatsApp message."""
    creds = get_whatsapp_credentials()
    
    url = f"https://graph.facebook.com/v18.0/{creds['phone_id']}/messages"
    
    headers = {
        "Authorization": f"Bearer {creds['token']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    print(f"???? Sending WhatsApp message...")
    print(f"   To: +{to_number}")
    print(f"   Message: {message_text}")
    print(f"   Phone Number ID: {creds['phone_id']}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"\n???? Response:")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   ??? Message sent successfully!")
        data = response.json()
        print(f"   Message ID: {data.get('messages', [{}])[0].get('id')}")
        return True
    else:
        print(f"   ??? Failed to send message")
        print(f"   Error: {response.text}")
        return False

if __name__ == "__main__":
    # Send test message to the test buyer number
    test_number = "2348099887766"  # Remove + prefix for API
    message = "???? Test message from TrustGuard WhatsApp Integration!\n\nIf you receive this, the webhook is working correctly."
    
    send_test_message(test_number, message)
