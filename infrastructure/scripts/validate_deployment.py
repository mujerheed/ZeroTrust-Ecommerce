#!/usr/bin/env python3
"""Quick smoke test for TrustGuard deployed endpoints.

Tests:
1. CEO registration (POST /auth/ceo/register)
2. Vendor login (POST /auth/vendor/login) - expect error without valid vendor
3. CEO OAuth URL generation (GET /ceo/oauth/meta/authorize)

Usage:
  python infrastructure/scripts/validate_deployment.py --api-url <API_GATEWAY_URL>

Example:
  python infrastructure/scripts/validate_deployment.py \
    --api-url https://p9yc4gwt9a.execute-api.us-east-1.amazonaws.com/Prod
"""
import argparse
import json
import sys
import requests

def test_ceo_register(base_url: str):
    """Test CEO registration endpoint."""
    url = f"{base_url}/auth/ceo/register"
    payload = {
        "name": "Smoke Test CEO",
        "email": "smoke-test@trustguard.dev",
        "phone": "+2348012345678",
        "business_name": "SmokeTestBiz"
    }
    
    print(f"[TEST] POST {url}")
    resp = requests.post(url, json=payload, timeout=10)
    print(f"  Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        return resp.status_code in [200, 201, 400, 409]  # 400/409 if already exists
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  Raw: {resp.text[:200]}")
        return False

def test_vendor_login(base_url: str):
    """Test vendor login (should fail gracefully for non-existent vendor)."""
    url = f"{base_url}/auth/vendor/login"
    payload = {
        "phone": "+2348099999999"
    }
    
    print(f"\n[TEST] POST {url}")
    resp = requests.post(url, json=payload, timeout=10)
    print(f"  Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        return resp.status_code in [200, 404]  # 404 expected for non-existent
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  Raw: {resp.text[:200]}")
        return False

def test_oauth_authorize(base_url: str):
    """Test OAuth authorization URL generation."""
    url = f"{base_url}/ceo/oauth/meta/authorize"
    
    print(f"\n[TEST] GET {url}")
    resp = requests.get(url, timeout=10)
    print(f"  Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        # Should return authorization_url if Meta secrets are set
        return resp.status_code in [200, 401]  # 401 if no auth header
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  Raw: {resp.text[:200]}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate TrustGuard deployment")
    parser.add_argument('--api-url', required=True, help='API Gateway base URL (without trailing /)')
    args = parser.parse_args()
    
    base_url = args.api_url.rstrip('/')
    
    print("=" * 60)
    print("TrustGuard Deployment Validation")
    print("=" * 60)
    print(f"API Base: {base_url}\n")
    
    results = []
    results.append(("CEO Registration", test_ceo_register(base_url)))
    results.append(("Vendor Login", test_vendor_login(base_url)))
    results.append(("CEO OAuth Authorize", test_oauth_authorize(base_url)))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All endpoints responding correctly!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check Lambda logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
