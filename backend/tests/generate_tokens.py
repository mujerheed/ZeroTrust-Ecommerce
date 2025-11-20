#!/usr/bin/env python3
"""Generate JWT tokens manually for testing Phase 2 endpoints"""

import jwt
import os
import uuid
from datetime import datetime, timedelta

# Get JWT secret from environment or use default
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")

def create_jwt_token(user_id: str, role: str) -> str:
    """Create a JWT token"""
    payload = {
        "sub": user_id,
        "role": role,
        "jti": str(uuid.uuid4()).replace('-', '')[:20],
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
    }
    
    if role == "CEO":
        payload["ceo_id"] = user_id
    
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# Generate tokens for testing
ceo_token = create_jwt_token("ceo_test_001", "CEO")
vendor_token = create_jwt_token("ceo_test_001", "VENDOR")

print("="*70)
print("JWT Tokens for Phase 2 Testing")
print("="*70)
print(f"\nCEO Token:\n{ceo_token}\n")
print(f"\nVendor Token:\n{vendor_token}\n")
print("="*70)
print("\nUse these tokens to test Phase 2 endpoints directly:")
print("  - CEO endpoints: Add header 'Authorization: Bearer <CEO_TOKEN>'")
print("  - Vendor endpoints: Add header 'Authorization: Bearer <VENDOR_TOKEN>'")
print("="*70)
