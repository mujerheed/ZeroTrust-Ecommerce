"""
Authentication business logic.
"""
from time import time
from .database import (
    get_user, anonymize_buyer_data, log_event, get_buyer_by_id,
    get_user_by_phone, get_user_by_email, create_ceo, create_vendor
)
from .otp_manager import request_otp, verify_otp, generate_otp, store_otp
from .token_manager import create_jwt
from common.logger import logger


def normalize_phone(phone: str) -> str:
    """
    Normalize Nigerian phone number to +234 format (SINGLE SOURCE OF TRUTH).
    
    All phone numbers stored in database MUST use +234 format.
    This function handles all user input variations.
    
    **Meta Sandbox Support:**
    - Maps +15556337144 (Meta test number) ↔ +2348155563371 (Nigerian test)
    - Bidirectional: works for both registration and lookups
    
    Args:
        phone: Phone number in various formats from user input
    
    Returns:
        Normalized phone number with +234 prefix (always 14 characters)
    
    Examples:
        "0906776624"       -> "+2349906776624"   (strip 0, add +234)
        "09067766240"      -> "+23409067766240"  (strip 0, add +234 - even if wrong length)
        "234906776624"     -> "+2349906776624"   (add +)
        "+234906776624"    -> "+2349906776624"   (already correct)
        "+234 906 776 624" -> "+2349906776624"   (remove spaces, keep format)
        "906776624"        -> "+2349906776624"   (assume missing prefix, add +234)
        "+15556337144"     -> "+2348155563371"   (Meta sandbox → Nigerian test)
        "+2348155563371"   -> "+2348155563371"   (Nigerian test → stored as-is)
    
    Note:
        Storage format: ALWAYS +234XXXXXXXXXX (14 chars total)
        User can input: 0XXX, 234XXX, +234XXX, or with spaces
        Meta sandbox numbers are automatically mapped for testing
    """
    from common.logger import logger
    
    # META SANDBOX MAPPING (for testing with Meta's test credentials)
    # Bidirectional mapping: Meta sandbox ↔ Nigerian test number
    META_SANDBOX_MAPPING = {
        "+15556337144": "+2348155563371",  # Meta sandbox → Nigerian test
        "15556337144": "+2348155563371",   # Without + prefix
        "+2348155563371": "+2348155563371", # Nigerian test → keep as-is
        "2348155563371": "+2348155563371",  # Without + prefix
    }
    
    # Step 1: Clean the input - remove ALL whitespace, dashes, parentheses
    phone = phone.strip()
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
    
    # Step 1.5: Check Meta sandbox mapping FIRST (before normalization)
    if phone in META_SANDBOX_MAPPING:
        mapped = META_SANDBOX_MAPPING[phone]
        logger.info(
            f"📱 Meta sandbox mapping applied: {phone} → {mapped}",
            extra={"original": phone, "mapped": mapped}
        )
        return mapped
    
    # Step 2: Normalize to +234 format
    if phone.startswith("+234"):
        # Already in correct format: "+234906776624"
        normalized = phone
    elif phone.startswith("234"):
        # Missing +: "234906776624" -> "+234906776624"
        normalized = "+" + phone
    elif phone.startswith("0"):
        # Local format: "0906776624" -> "+2349906776624"
        # Strip the leading 0 and add +234
        normalized = "+234" + phone[1:]
    else:
        # No prefix at all: "906776624" -> "+2349906776624"
        # Assume it's the digits after country code
        normalized = "+234" + phone
    
    # Step 3: Log warning if length is not 14 (expected: +234 + 10 digits)
    if len(normalized) != 14:
        logger.warning(
            f"Phone normalization: unusual length after normalization. "
            f"Input: '{phone[:4]}***', Output: '{normalized[:8]}***', Length: {len(normalized)} (expected 14)",
            extra={
                "input_phone": phone[:4] + "***",
                "output_phone": normalized[:8] + "***",
                "length": len(normalized)
            }
        )
    
    return normalized


def register_ceo(name: str, phone: str, email: str) -> dict:
    """
    Register a new CEO (self-registration).
    Returns user_id for OTP verification.
    """
    # Generate unique CEO ID
    ceo_id = f"ceo_{int(time() * 1000)}"
    
    # Create CEO in DynamoDB USERS_TABLE
    create_ceo(ceo_id, name, phone, email)
    
    # Send OTP for verification
    dev_otp = None
    try:
        otp_result = request_otp(
            user_id=ceo_id,
            role="CEO",
            contact=email, # Default to email for CEO registration OTP
            platform=None,
            phone=phone
        )
        dev_otp = otp_result.get('dev_otp')
    except Exception as e:
        logger.error(f"Failed to send OTP during CEO registration: {e}")
        # We still return success to avoid leaking info, but log the error
        
    return {
        "ceo_id": ceo_id,
        "status": "pending_verification",
        "dev_otp": dev_otp
    }


def login_ceo(contact: str) -> str:
    """
    Initiate CEO login via OTP.
    
    Args:
        contact: Phone number or email address
    
    Returns:
        ceo_id if user found and OTP sent
    
    Raises:
        ValueError: If CEO not found or inactive
    """
    # Determine if contact is email or phone
    is_email = "@" in contact
    
    # Look up CEO in database
    if is_email:
        ceo = get_user_by_email(contact, role="CEO")
    else:
        ceo = get_user_by_phone(contact, role="CEO")
    
    if not ceo:
        logger.warning(f"CEO login attempt with unknown contact: {contact[:4]}***")
        raise ValueError("CEO account not found. Please register first.")
    
    ceo_id = ceo.get("user_id")
    
    # Check if CEO account is active
    if ceo.get("status") != "active":
        logger.warning(f"Inactive CEO login attempt: {ceo_id}")
        raise ValueError("CEO account is not active. Please contact support.")
    
    # Generate and send OTP using request_otp helper
    try:
        result = request_otp(
            user_id=ceo_id,
            role="CEO",
            contact=contact,
            platform=None,
            phone=ceo.get("phone") if is_email else contact
        )
        
        logger.info(f"CEO OTP sent successfully", extra={
            "ceo_id": ceo_id,
            "delivery_method": result.get("delivery_method")
        })
        
        return {
            "ceo_id": ceo_id,
            "dev_otp": result.get('dev_otp')
        }
    except Exception as e:
        logger.error(f"Failed to send CEO OTP: {e}", extra={"ceo_id": ceo_id})
        raise ValueError(f"Failed to send OTP: {str(e)}")


def login_vendor(phone: str) -> str:
    """
    Initiate vendor login via OTP.
    
    Args:
        phone: Vendor's registered phone number
    
    Returns:
        vendor_id if user found and OTP sent
    
    Raises:
        ValueError: If vendor not found or inactive
    """
    # Normalize phone number to +234 format
    normalized_phone = normalize_phone(phone)
    
    logger.info(
        f"Vendor login attempt - Original: {phone[:4]}***, Normalized: {normalized_phone[:8]}***",
        extra={"original_phone": phone[:4] + "***", "normalized_phone": normalized_phone[:8] + "***"}
    )
    
    # Look up vendor in database
    vendor = get_user_by_phone(normalized_phone, role="Vendor")
    
    if not vendor:
        logger.warning(
            f"Vendor login attempt with unknown phone. "
            f"Original: {phone[:4]}***, Normalized: {normalized_phone[:8]}*** not found in database.",
            extra={"original_phone": phone[:4] + "***", "normalized_phone": normalized_phone[:8] + "***"}
        )
        raise ValueError("Vendor account not found. Please contact your CEO to register.")
    
    vendor_id = vendor.get("user_id")
    
    # Check if vendor account is active
    if vendor.get("status") != "active":
        logger.warning(f"Inactive vendor login attempt: {vendor_id}")
        raise ValueError("Vendor account is not active. Please contact your CEO.")
    
    # Generate and send OTP using request_otp helper
    try:
        result = request_otp(
            user_id=vendor_id,
            role="Vendor",
            contact=normalized_phone,  # Use normalized phone for OTP delivery
            platform=None,
            phone=normalized_phone  # Use normalized phone
        )
        
        logger.info(f"Vendor OTP sent successfully", extra={
            "vendor_id": vendor_id,
            "delivery_method": result.get("delivery_method")
        })
        
        return {
            "vendor_id": vendor_id,
            "dev_otp": result.get('dev_otp')
        }
    except Exception as e:
        logger.error(f"Failed to send Vendor OTP: {e}", extra={"vendor_id": vendor_id})
        raise ValueError(f"Failed to send OTP: {str(e)}")


def verify_otp_universal(user_id: str, otp: str) -> dict:
    """
    Universal OTP verification for all user types.
    Returns JWT token if valid.
    
    Args:
        user_id: User ID (ceo_id, vendor_id, or buyer_id)
        otp: OTP code to verify
    
    Returns:
        Dict with validation result, token, and role
    
    Raises:
        ValueError: If OTP is invalid or user not found
    """
    logger.info(f"[DEBUG] verify_otp_universal: user_id={user_id}, otp_length={len(otp)}")
    
    # Verify OTP
    logger.info(f"[DEBUG] Calling verify_otp from otp_manager")
    result = verify_otp(user_id, otp)
    logger.info(f"[DEBUG] verify_otp result: {result}")
    
    if not result.get("valid"):
        error_msg = result.get("error", "Invalid or expired OTP")
        logger.warning(f"[DEBUG] OTP invalid: {error_msg}")
        raise ValueError(error_msg)
    
    # Get role from OTP verification result
    role = result.get("role")
    if not role:
        logger.error(f"OTP verified but no role returned: {user_id}")
        raise ValueError("Role not found in OTP record")
    
    # Get user's ceo_id for multi-tenancy support
    user = get_user(user_id)
    ceo_id = None
    if user:
        ceo_id = user.get("ceo_id")
        
        # Mark user as verified on first successful OTP login
        # This applies to CEO (on registration) and Vendor (on first login)
        if user.get("verified") == False and role in ["CEO", "Vendor"]:
            from .database import update_user
            update_user(user_id, {"verified": True})
            logger.info(f"{role} marked as verified on successful OTP verification", extra={
                "user_id": user_id,
                "role": role
            })
    
    logger.info(f"[DEBUG] Creating JWT token for user_id={user_id}, role={role}, ceo_id={ceo_id}")
    # Generate JWT token with ceo_id for multi-tenancy
    token = create_jwt(user_id, role, ceo_id=ceo_id)
    
    logger.info(f"OTP verified successfully", extra={
        "user_id": user_id,
        "role": role
    })
    
    return {"valid": True, "token": token, "role": role}


def create_vendor_account(name: str, phone: str, email: str, created_by: str) -> str:
    """
    CEO creates a vendor account.
    Returns vendor_id.
    """
    # Create vendor in DynamoDB USERS_TABLE
    vendor_id = f"vendor_{int(time() * 1000)}"
    create_vendor(vendor_id, name, phone, email, created_by)
    
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
    # Verify OTP
    result = verify_otp(user_id, otp)
    if not result.get("valid"):
        # Publish CloudWatch metric for OTP failure
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch')
            cloudwatch.put_metric_data(
                Namespace='TrustGuard/Auth',
                MetricData=[{
                    'MetricName': 'OTPVerificationFailures',
                    'Value': 1,
                    'Unit': 'Count'
                }]
            )
        except Exception as e:
            logger.warning(f"Failed to publish OTP failure metric: {str(e)}")
        
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

