"""
Authentication business logic.
"""
from time import time
from .database import get_user, anonymize_buyer_data, log_event, get_buyer_by_id
from .otp_manager import request_otp, verify_otp, generate_otp, store_otp
from .token_manager import create_jwt
from common.logger import logger


def register_ceo(name: str, phone: str, email: str) -> dict:
    """
    Register a new CEO (self-registration).
    Returns user_id for OTP verification.
    """
    # TODO: Create CEO in DynamoDB USERS_TABLE
    ceo_id = f"ceo_{int(time() * 1000)}"
    # Mock implementation - in production, save to DynamoDB
    return {"ceo_id": ceo_id, "status": "pending_verification"}


def login_ceo(phone: str) -> dict:
    """
    Initiate CEO login via OTP.
    """
    # TODO: Fetch CEO by phone from DynamoDB
    # For now, mock response
    return {"status": "otp_sent", "message": "OTP sent to your phone"}


def login_vendor(phone: str) -> dict:
    """
    Initiate vendor login via OTP.
    """
    # TODO: Fetch vendor by phone from DynamoDB
    return {"status": "otp_sent", "message": "OTP sent to your phone"}


def verify_otp_universal(user_id: str, otp: str, role: str) -> dict:
    """
    Universal OTP verification for all user types.
    Returns JWT token if valid.
    """
    result = verify_otp(user_id, otp)
    if not result.get("valid"):
        return {"valid": False, "message": "Invalid or expired OTP"}
    
    # Generate JWT token
    token = create_jwt(user_id, role)
    return {"valid": True, "token": token, "role": role}


def create_vendor_account(name: str, phone: str, email: str, created_by: str) -> str:
    """
    CEO creates a vendor account.
    Returns vendor_id.
    """
    # TODO: Create vendor in DynamoDB USERS_TABLE
    vendor_id = f"vendor_{int(time() * 1000)}"
    # Mock implementation - in production, save to DynamoDB with created_by (ceo_id)
    return vendor_id


def register_user(email: str, phone: str, name: str) -> str:
    """
    (Optional) Implement user creation in USERS_TABLE.
    """
    # TODO: add to DynamoDB users table
    user_id = f"user_{int(time.time())}"
    return user_id  # return the new user_id

def login_user(user_id: str) -> bool:
    """
    Initiate OTP process for login.
    """
    user = get_user(user_id)
    if not user:
        raise Exception("User not found")
    contact = user.get("contact") or user.get("email")
    return request_otp(user_id, user.get("role", "Buyer"), contact)

def verify_otp_code(user_id: str, otp: str) -> str:
    """
    Verify OTP and return a JWT if successful.
    """
    result = verify_otp(user_id, otp)
    if not result.get("valid"):
        raise Exception("Invalid or expired OTP")
    return create_jwt(user_id, result["role"])


def request_data_erasure_otp(buyer_id: str) -> dict:
    """
    Generate OTP for data erasure verification (GDPR/NDPR compliance).
    
    This is a high-security action requiring explicit OTP verification before
    permanently anonymizing buyer data.
    
    Args:
        buyer_id: Buyer identifier requesting data erasure
    
    Returns:
        Dict with OTP sent confirmation
    
    Raises:
        ValueError: If buyer not found or already anonymized
    """
    # Verify buyer exists
    buyer = get_buyer_by_id(buyer_id)
    if not buyer:
        raise ValueError(f"Buyer {buyer_id} not found")
    
    if buyer.get("anonymized"):
        raise ValueError("Account already anonymized. No further action needed.")
    
    # Generate 8-character OTP (same format as buyer OTP)
    otp = generate_otp('Buyer')
    
    # Store OTP with 5-minute TTL
    store_otp(buyer_id, otp, 'Buyer')
    
    logger.info(
        "Data erasure OTP generated",
        extra={
            'buyer_id': buyer_id,
            'platform': buyer.get('platform', 'unknown')
        }
    )
    
    # Log audit event
    log_event(
        user_id=buyer_id,
        action="DATA_ERASURE_OTP_REQUESTED",
        status="success",
        message="User requested OTP for data erasure"
    )
    
    return {
        "status": "otp_sent",
        "message": "OTP sent for data erasure verification",
        "buyer_id": buyer_id,
        "otp_ttl_seconds": 300,  # 5 minutes
        # In development, return OTP for testing (remove in production)
        "dev_otp": otp if logger.level <= 10 else None
    }


def erase_buyer_data(buyer_id: str, otp: str) -> dict:
    """
    Erase buyer PII after OTP verification (GDPR/NDPR "Right to be Forgotten").
    
    Process:
    1. Verify OTP
    2. Anonymize buyer PII (name → [REDACTED], phone → [REDACTED])
    3. Remove delivery_address, email, metadata
    4. Preserve anonymized order history for legal/forensic requirements
    5. Log DATA_ERASURE_CONFIRMED audit event
    
    Args:
        buyer_id: Buyer identifier
        otp: OTP code for verification
    
    Returns:
        Dict with erasure confirmation
    
    Raises:
        ValueError: If buyer not found, OTP invalid, or already anonymized
    """
    # Verify buyer exists
    buyer = get_buyer_by_id(buyer_id)
    if not buyer:
        raise ValueError(f"Buyer {buyer_id} not found")
    
    if buyer.get("anonymized"):
        raise ValueError("Account already anonymized")
    
    # Verify OTP
    otp_result = verify_otp(buyer_id, otp)
    if not otp_result or not otp_result.get("valid"):
        # Log failed attempt
        log_event(
            user_id=buyer_id,
            action="DATA_ERASURE_FAILED",
            status="error",
            message="Invalid OTP provided for data erasure"
        )
        raise ValueError("Invalid or expired OTP. Data erasure request denied.")
    
    # Anonymize buyer data
    try:
        anonymized_buyer = anonymize_buyer_data(buyer_id)
        
        logger.info(
            "Buyer data anonymized successfully",
            extra={
                'buyer_id': buyer_id,
                'anonymized_at': anonymized_buyer.get('anonymized_at')
            }
        )
        
        # Log successful erasure (CRITICAL audit event)
        log_event(
            user_id=buyer_id,
            action="DATA_ERASURE_CONFIRMED",
            status="success",
            message="Buyer PII anonymized per GDPR/NDPR data erasure request",
            meta={
                "anonymized_fields": ["name", "phone", "email", "delivery_address", "meta"],
                "preserved_fields": ["user_id", "role", "platform", "ceo_id", "order_references"],
                "anonymized_at": anonymized_buyer.get('anonymized_at'),
                "compliance_framework": "GDPR/NDPR"
            }
        )
        
        return {
            "status": "success",
            "message": "Your personal data has been permanently erased",
            "buyer_id": buyer_id,
            "anonymized_at": anonymized_buyer.get('anonymized_at'),
            "preserved_data": "Anonymized order history retained for legal compliance",
            "compliance": "GDPR/NDPR Right to be Forgotten"
        }
    
    except Exception as e:
        # Log failure
        log_event(
            user_id=buyer_id,
            action="DATA_ERASURE_FAILED",
            status="error",
            message=f"Data erasure failed: {str(e)}"
        )
        raise ValueError(f"Failed to anonymize data: {str(e)}")

