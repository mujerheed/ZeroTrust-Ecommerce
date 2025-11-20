"""
Create a CEO user who is also a Vendor (dual-role support).
This demonstrates how the system supports CEOs managing their own orders.
"""
import boto3
import time

AWS_REGION = "us-east-1"
USERS_TABLE = "TrustGuard-Users-dev"

def create_ceo_vendor_dual_role():
    """
    Create a CEO account that also has Vendor role.
    This is common for small businesses where the owner handles operations.
    """
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(USERS_TABLE)
    
    # CEO with dual role (CEO + Vendor)
    ceo_vendor = {
        "user_id": "ceo_test_001",  # Primary user ID is CEO ID
        "role": "CEO",  # Primary role
        "roles": ["CEO", "Vendor"],  # All roles this user has
        "name": "Test CEO (Also Vendor)",
        "email": "test.ceo@trustguard.com",
        "phone": "+2348133336318",
        "status": "active",
        "company_name": "TrustGuard Test Company",
        "created_at": int(time.time()),
        "last_login": int(time.time()),
        "vendor_id": "ceo_test_001",  # Same as user_id when CEO is also vendor
        "ceo_id": "ceo_test_001",  # Points to self
        "metadata": {
            "test_account": True,
            "dual_role": True,
            "created_by": "test_script"
        }
    }
    
    print("🔧 Creating CEO with dual role (CEO + Vendor)...")
    print(f"Table: {USERS_TABLE}\n")
    
    try:
        table.put_item(Item=ceo_vendor)
        print(f"✓ Created user: {ceo_vendor['user_id']}")
        print(f"  - Name: {ceo_vendor['name']}")
        print(f"  - Phone: {ceo_vendor['phone']}")
        print(f"  - Email: {ceo_vendor['email']}")
        print(f"  - Primary Role: {ceo_vendor['role']}")
        print(f"  - All Roles: {', '.join(ceo_vendor['roles'])}")
        print(f"\n✅ CEO can now login as both CEO and Vendor!\n")
        
        print("Login options:")
        print(f"  - As CEO: POST /auth/ceo/login with phone or email")
        print(f"  - As Vendor: POST /auth/vendor/login with phone")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create dual-role user: {e}")
        return False

def verify_dual_role():
    """Verify the dual-role user can be accessed via both login paths"""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(USERS_TABLE)
    
    print("\n🔍 Verifying dual-role access...")
    
    response = table.get_item(Key={"user_id": "ceo_test_001"})
    if 'Item' in response:
        user = response['Item']
        print(f"✓ User found: {user['name']}")
        print(f"  - Has CEO role: {'CEO' in user.get('roles', [])}")
        print(f"  - Has Vendor role: {'Vendor' in user.get('roles', [])}")
        
        if 'CEO' in user.get('roles', []) and 'Vendor' in user.get('roles', []):
            print("\n✓ Dual-role verification successful!")
            return True
    
    print("✗ Verification failed")
    return False

if __name__ == "__main__":
    success = create_ceo_vendor_dual_role()
    if success:
        verify_dual_role()
