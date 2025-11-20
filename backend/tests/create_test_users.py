"""
Create test CEO and Vendor accounts in DynamoDB for testing
"""
import boto3
import time
import hashlib
from datetime import datetime

# Configuration
AWS_REGION = "us-east-1"
USERS_TABLE = "TrustGuard-Users-dev"

# Test user data
TEST_CEO = {
    "user_id": "ceo_test_001",
    "role": "CEO",
    "name": "Test CEO",
    "email": "test.ceo@trustguard.com",
    "phone": "+2348133336318",
    "status": "active",
    "company_name": "TrustGuard Test Company",
    "created_at": int(time.time()),
    "last_login": int(time.time()),
    "metadata": {
        "test_account": True,
        "created_by": "test_script"
    }
}

TEST_VENDOR = {
    "user_id": "vendor_test_001",
    "role": "Vendor",
    "name": "Test Vendor",
    "email": "test.vendor@trustguard.com",
    "phone": "+2348133336318",
    "status": "active",
    "ceo_id": "ceo_test_001",  # Linked to test CEO
    "created_at": int(time.time()),
    "created_by": "ceo_test_001",
    "last_login": int(time.time()),
    "metadata": {
        "test_account": True,
        "created_by": "test_script"
    }
}

def create_test_users():
    """Create test CEO and Vendor in DynamoDB"""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(USERS_TABLE)
    
    print("🔧 Creating test users in DynamoDB...")
    print(f"Table: {USERS_TABLE}")
    print(f"Region: {AWS_REGION}\n")
    
    # Create CEO
    try:
        print(f"Creating CEO: {TEST_CEO['user_id']}")
        print(f"  - Name: {TEST_CEO['name']}")
        print(f"  - Phone: {TEST_CEO['phone']}")
        print(f"  - Email: {TEST_CEO['email']}")
        
        table.put_item(Item=TEST_CEO)
        print("✓ CEO account created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create CEO: {e}\n")
        return False
    
    # Create Vendor
    try:
        print(f"Creating Vendor: {TEST_VENDOR['user_id']}")
        print(f"  - Name: {TEST_VENDOR['name']}")
        print(f"  - Phone: {TEST_VENDOR['phone']}")
        print(f"  - Email: {TEST_VENDOR['email']}")
        print(f"  - CEO ID: {TEST_VENDOR['ceo_id']}")
        
        table.put_item(Item=TEST_VENDOR)
        print("✓ Vendor account created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create Vendor: {e}\n")
        return False
    
    print("="*80)
    print("✅ Test accounts created successfully!")
    print("="*80)
    print("\nYou can now test authentication with:")
    print(f"\nCEO Login:")
    print(f"  Phone: {TEST_CEO['phone']}")
    print(f"  Email: {TEST_CEO['email']}")
    print(f"\nVendor Login:")
    print(f"  Phone: {TEST_VENDOR['phone']}")
    print("\n" + "="*80)
    
    return True

def verify_test_users():
    """Verify test users exist in DynamoDB"""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(USERS_TABLE)
    
    print("\n🔍 Verifying test users...")
    
    # Check CEO
    response = table.get_item(Key={"user_id": TEST_CEO['user_id']})
    if 'Item' in response:
        print(f"✓ CEO found: {response['Item']['name']} ({response['Item']['phone']})")
    else:
        print(f"✗ CEO not found")
        return False
    
    # Check Vendor
    response = table.get_item(Key={"user_id": TEST_VENDOR['user_id']})
    if 'Item' in response:
        print(f"✓ Vendor found: {response['Item']['name']} ({response['Item']['phone']})")
    else:
        print(f"✗ Vendor not found")
        return False
    
    print("✓ All test users verified\n")
    return True

if __name__ == "__main__":
    if create_test_users():
        verify_test_users()
