#!/usr/bin/env python3
"""Seed or update TrustGuard Secrets Manager entries.

This script:
  1. Reads CloudFormation stack outputs to discover secret ARNs
  2. Fetches existing secret JSON (app/meta)
  3. Optionally rotates JWT secret (32-char, no punctuation)
  4. Updates Meta secret with APP_ID / APP_SECRET values provided via CLI args

Usage:
  python infrastructure/scripts/seed_secrets.py \
      --stack TrustGuard-Dev \
      --region us-east-1 \
      --app-id <META_APP_ID> \
      --app-secret <META_APP_SECRET> \
      [--rotate-jwt]

Requires:
  - AWS credentials with secretsmanager:GetSecretValue / UpdateSecret permissions
  - boto3 installed (present in backend requirements)

Exit codes:
  0 success
  1 argument or runtime error
  2 AWS API error
"""
from __future__ import annotations
import argparse
import json
import os
import random
import string
import sys
from typing import Dict

import boto3
from botocore.exceptions import ClientError

JWT_KEY_NAME = "JWT_SECRET"

def gen_jwt_secret(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(alphabet) for _ in range(length))

def get_stack_outputs(cf, stack_name: str) -> Dict[str, str]:
    try:
        resp = cf.describe_stacks(StackName=stack_name)
    except ClientError as e:
        print(f"[ERROR] describe_stacks failed: {e}")
        sys.exit(2)
    stacks = resp.get('Stacks', [])
    if not stacks:
        print(f"[ERROR] Stack '{stack_name}' not found")
        sys.exit(2)
    outputs = stacks[0].get('Outputs', [])
    return {o['OutputKey']: o['OutputValue'] for o in outputs}

def fetch_secret_value(sm, arn: str) -> Dict:
    try:
        resp = sm.get_secret_value(SecretId=arn)
        raw = resp.get('SecretString', '{}')
        return json.loads(raw or '{}')
    except ClientError as e:
        print(f"[ERROR] get_secret_value failed for {arn}: {e}")
        sys.exit(2)

def update_secret(sm, arn: str, payload: Dict):
    try:
        sm.update_secret(SecretId=arn, SecretString=json.dumps(payload))
        print(f"[OK] Updated secret: {arn}")
    except ClientError as e:
        print(f"[ERROR] update_secret failed for {arn}: {e}")
        sys.exit(2)

def main():
    parser = argparse.ArgumentParser(description="Seed TrustGuard secrets")
    parser.add_argument('--stack', default='TrustGuard-Dev', help='CloudFormation stack name')
    parser.add_argument('--region', default=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'), help='AWS region')
    parser.add_argument('--app-id', required=True, help='Meta APP_ID value')
    parser.add_argument('--app-secret', required=True, help='Meta APP_SECRET value')
    parser.add_argument('--whatsapp-token', help='WhatsApp Business API access token (optional)')
    parser.add_argument('--whatsapp-phone-id', help='WhatsApp Business Phone Number ID (optional)')
    parser.add_argument('--instagram-token', help='Instagram Page Access Token (optional)')
    parser.add_argument('--instagram-page-id', help='Instagram Page ID (optional)')
    parser.add_argument('--rotate-jwt', action='store_true', help='Generate a new JWT secret')
    args = parser.parse_args()

    cf = boto3.client('cloudformation', region_name=args.region)
    sm = boto3.client('secretsmanager', region_name=args.region)

    outputs = get_stack_outputs(cf, args.stack)

    app_arn = outputs.get('SecretsArn')
    meta_arn = outputs.get('MetaSecretsArn')
    if not app_arn or not meta_arn:
        print('[ERROR] Missing secret ARNs in stack outputs. Ensure stack deployed and outputs exist.')
        sys.exit(1)

    print(f"[INFO] App secret ARN:  {app_arn}")
    print(f"[INFO] Meta secret ARN: {meta_arn}")

    # Fetch existing app secret JSON (may only contain JWT_SECRET)
    app_secret_json = fetch_secret_value(sm, app_arn)
    if JWT_KEY_NAME not in app_secret_json:
        # stack template used GenerateSecretString -> rename scenario
        existing_jwt = None
    else:
        existing_jwt = app_secret_json[JWT_KEY_NAME]

    if args.rotate_jwt or not existing_jwt:
        new_jwt = gen_jwt_secret()
        app_secret_json[JWT_KEY_NAME] = new_jwt
        print('[INFO] Rotated JWT secret')
    else:
        print('[INFO] Preserving existing JWT secret')

    update_secret(sm, app_arn, app_secret_json)

    # Fetch & update meta secret
    meta_secret_json = fetch_secret_value(sm, meta_arn)
    meta_secret_json['APP_ID'] = args.app_id
    meta_secret_json['APP_SECRET'] = args.app_secret
    
    # Add WhatsApp credentials if provided
    if args.whatsapp_token:
        meta_secret_json['WHATSAPP_ACCESS_TOKEN'] = args.whatsapp_token
        print('[INFO] Added WhatsApp access token')
    if args.whatsapp_phone_id:
        meta_secret_json['WHATSAPP_PHONE_NUMBER_ID'] = args.whatsapp_phone_id
        print('[INFO] Added WhatsApp phone number ID')
    
    # Add Instagram credentials if provided
    if args.instagram_token:
        meta_secret_json['INSTAGRAM_ACCESS_TOKEN'] = args.instagram_token
        print('[INFO] Added Instagram access token')
    if args.instagram_page_id:
        meta_secret_json['INSTAGRAM_PAGE_ID'] = args.instagram_page_id
        print('[INFO] Added Instagram page ID')
    
    # Prepare tenant tokens placeholder (for multi-CEO OAuth)
    meta_secret_json.setdefault('ceo_oauth_tokens', {})  # ceo_id -> {access_token, expires_at, phone_id, page_id}

    update_secret(sm, meta_arn, meta_secret_json)

    print('\n[SUMMARY]')
    print(f"App secret keys: {list(app_secret_json.keys())}")
    print(f"Meta secret keys: {list(meta_secret_json.keys())}")
    print('[DONE] Secrets seeded successfully')

if __name__ == '__main__':
    main()
