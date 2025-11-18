""""""

JWT token creation and validation with multi-tenant isolation.JWT token creation and validation with multi-tenant isolation.



This module provides:This module provides:

- Role-based JWT creation with ceo_id for multi-tenancy- Role-based JWT creation with ceo_id for multi-tenancy

- Role-specific token expiry (Buyer: 10min, Vendor/CEO: 30min)- Role-specific token expiry (Buyer: 10min, Vendor/CEO: 30min)

- Token revocation tracking via unique jti (JWT ID)- Token revocation tracking via unique jti (JWT ID)

- Integration with AWS Secrets Manager for JWT secret- Integration with AWS Secrets Manager for JWT secret

""""""



import jwtimport jwt

import timeimport time

import secretsimport secrets

from typing import Dict, Any, Optionalfrom datetime import datetime, timedelta

from common.config import settingsfrom typing import Dict, Any, Optional

from common.logger import loggerfrom common.config import settings

from common.logger import logger

ALGORITHM = "HS256"

ALGORITHM = "HS256"

# Role-based token expiry

TOKEN_EXPIRY_MINUTES = {# Role-based token expiry

    'BUYER': 10,    # Short-lived for chat-based authenticationTOKEN_EXPIRY_MINUTES = {

    'VENDOR': 30,   # Dashboard session    'BUYER': 10,    # Short-lived for chat-based authentication

    'CEO': 30       # Dashboard session    'VENDOR': 30,   # Dashboard session

}    'CEO': 30       # Dashboard session

}



def _get_secret_key() -> str:

    """Get JWT secret from Secrets Manager (fresh fetch each time)."""def _get_secret_key() -> str:

    return settings.get_jwt_secret()    """Get JWT secret from Secrets Manager (fresh fetch each time)."""

    return settings.get_jwt_secret()



def create_jwt(

    user_id: str,def create_jwt(

    role: str,    user_id: str,

    ceo_id: Optional[str] = None,    role: str,

    expires_minutes: Optional[int] = None    ceo_id: Optional[str] = None,

) -> str:    expires_minutes: Optional[int] = None

    """) -> str:

    Generate a signed JWT with multi-tenant isolation support.    """

        Generate a signed JWT with multi-tenant isolation support.

    Args:    

        user_id (str): User identifier (buyer_id, vendor_id, or ceo_id)    Args:

        role (str): User role ('Buyer', 'Vendor', or 'CEO')        user_id (str): User identifier (buyer_id, vendor_id, or ceo_id)

        ceo_id (str, optional): CEO identifier for multi-tenant isolation.        role (str): User role ('Buyer', 'Vendor', or 'CEO')

                                Required for Buyer and Vendor roles.        ceo_id (str, optional): CEO identifier for multi-tenant isolation.

        expires_minutes (int, optional): Custom expiry time. If not provided,                                Required for Buyer and Vendor roles.

                                         uses role-based default.        expires_minutes (int, optional): Custom expiry time. If not provided,

                                             uses role-based default.

    Returns:    

        str: Signed JWT token    Returns:

            str: Signed JWT token

    Raises:    

        ValueError: If ceo_id is missing for Buyer/Vendor roles    Raises:

            ValueError: If ceo_id is missing for Buyer/Vendor roles

    Example:    

        >>> create_jwt('wa_1234567890', 'Buyer', ceo_id='ceo_abc123')    Example:

        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'        >>> create_jwt('wa_1234567890', 'Buyer', ceo_id='ceo_abc123')

    """        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

    role_upper = role.upper()    """

        role_upper = role.upper()

    # Validate ceo_id requirement for multi-tenancy    

    if role_upper in ['BUYER', 'VENDOR'] and not ceo_id:    # Validate ceo_id requirement for multi-tenancy

        raise ValueError(f"{role} tokens require ceo_id for multi-tenant isolation")    if role_upper in ['BUYER', 'VENDOR'] and not ceo_id:

            raise ValueError(f"{role} tokens require ceo_id for multi-tenant isolation")

    # Determine expiry time    

    if expires_minutes is None:    # Determine expiry time

        expires_minutes = TOKEN_EXPIRY_MINUTES.get(role_upper, 30)    if expires_minutes is None:

            expires_minutes = TOKEN_EXPIRY_MINUTES.get(role_upper, 30)

    # Calculate timestamps    

    now = int(time.time())    # Calculate timestamps

    exp_time = now + (expires_minutes * 60)    now = int(time.time())

        exp_time = now + (expires_minutes * 60)

    # Build JWT payload    

    payload = {    # Build JWT payload

        'sub': user_id,           # Subject (user identifier)    payload = {

        'role': role,             # User role for RBAC        'sub': user_id,           # Subject (user identifier)

        'iat': now,               # Issued at timestamp        'role': role,             # User role for RBAC

        'exp': exp_time,          # Expiration timestamp        'iat': now,               # Issued at timestamp

        'jti': secrets.token_hex(16)  # Unique token ID for revocation tracking        'exp': exp_time,          # Expiration timestamp

    }        'jti': secrets.token_hex(16)  # Unique token ID for revocation tracking

        }

    # Add ceo_id for multi-tenant isolation (except for CEO role)    

    if ceo_id and role_upper != 'CEO':    # Add ceo_id for multi-tenant isolation (except for CEO role)

        payload['ceo_id'] = ceo_id    if ceo_id and role_upper != 'CEO':

            payload['ceo_id'] = ceo_id

    # Get fresh JWT secret and sign token    

    secret_key = _get_secret_key()    # Get fresh JWT secret and sign token

    token = jwt.encode(payload, secret_key, algorithm=ALGORITHM)    secret_key = _get_secret_key()

        token = jwt.encode(payload, secret_key, algorithm=ALGORITHM)

    logger.info(    

        f"JWT created: user_id={user_id}, role={role}, "    logger.info(

        f"ceo_id={ceo_id}, expires_in={expires_minutes}min, jti={payload['jti'][:8]}..."        f"JWT created: user_id={user_id}, role={role}, "

    )        f"ceo_id={ceo_id}, expires_in={expires_minutes}min, jti={payload['jti'][:8]}..."

        )

    return token    

    return token



def decode_jwt(token: str) -> Optional[Dict[str, Any]]:

    """def decode_jwt(token: str) -> Optional[Dict[str, Any]]:

    Decode and validate a JWT token.    """

        Decode and validate a JWT token.

    Args:    

        token (str): JWT token string    Args:

            token (str): JWT token string

    Returns:    

        Optional[Dict[str, Any]]: Decoded payload with user info, or None if invalid    Returns:

            Optional[Dict[str, Any]]: Decoded payload with user info, or None if invalid

    Example:    

        >>> payload = decode_jwt(token)    Example:

        >>> print(payload['sub'], payload['role'], payload.get('ceo_id'))        >>> payload = decode_jwt(token)

        'wa_1234567890' 'Buyer' 'ceo_abc123'        >>> print(payload['sub'], payload['role'], payload.get('ceo_id'))

    """        'wa_1234567890' 'Buyer' 'ceo_abc123'

    try:    """

        # Get fresh JWT secret for validation    try:

        secret_key = _get_secret_key()        # Get fresh JWT secret for validation

        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])        secret_key = _get_secret_key()

                payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

        logger.debug(        

            f"JWT decoded: user_id={payload.get('sub')}, "        logger.debug(

            f"role={payload.get('role')}, jti={payload.get('jti', '')[:8]}..."            f"JWT decoded: user_id={payload.get('sub')}, "

        )            f"role={payload.get('role')}, jti={payload.get('jti', '')[:8]}..."

                )

        return payload        

                return payload

    except jwt.ExpiredSignatureError:        

        logger.warning("JWT validation failed: Token expired")    except jwt.ExpiredSignatureError:

        return None        logger.warning("JWT validation failed: Token expired")

    except jwt.InvalidTokenError as e:        return None

        logger.warning(f"JWT validation failed: {str(e)}")    except jwt.InvalidTokenError as e:

        return None        logger.warning(f"JWT validation failed: {str(e)}")

        return None



def verify_token_role(token: str, required_role: str) -> Optional[str]:

    """def verify_token_role(token: str, required_role: str) -> Optional[str]:

    Verify JWT token and check if it has the required role.    """

        Verify JWT token and check if it has the required role.

    Args:    

        token (str): JWT token string    Args:

        required_role (str): Required role ('Buyer', 'Vendor', or 'CEO')        token (str): JWT token string

            required_role (str): Required role ('Buyer', 'Vendor', or 'CEO')

    Returns:    

        Optional[str]: user_id if token is valid and has required role, None otherwise    Returns:

            Optional[str]: user_id if token is valid and has required role, None otherwise

    Example:    

        >>> vendor_id = verify_token_role(token, 'Vendor')    Example:

        >>> if vendor_id:        >>> vendor_id = verify_token_role(token, 'Vendor')

        ...     # Proceed with vendor-specific logic        >>> if vendor_id:

    """        ...     # Proceed with vendor-specific logic

    payload = decode_jwt(token)    """

        payload = decode_jwt(token)

    if not payload:    

        return None    if not payload:

            return None

    if payload.get('role', '').upper() != required_role.upper():    

        logger.warning(    if payload.get('role', '').upper() != required_role.upper():

            f"Role mismatch: expected {required_role}, got {payload.get('role')}"        logger.warning(

        )            f"Role mismatch: expected {required_role}, got {payload.get('role')}"

        return None        )

            return None

    return payload.get('sub')    

    return payload.get('sub')



def extract_ceo_id(token: str) -> Optional[str]:

    """def extract_ceo_id(token: str) -> Optional[str]:

    Extract ceo_id from JWT token for multi-tenant operations.    """

        Extract ceo_id from JWT token for multi-tenant operations.

    Args:    

        token (str): JWT token string    Args:

            token (str): JWT token string

    Returns:    

        Optional[str]: ceo_id if present in token, None otherwise    Returns:

            Optional[str]: ceo_id if present in token, None otherwise

    Note:    

        CEO tokens don't include ceo_id (they ARE the CEO).    Note:

        Buyer and Vendor tokens must include ceo_id.        CEO tokens don't include ceo_id (they ARE the CEO).

    """        Buyer and Vendor tokens must include ceo_id.

    payload = decode_jwt(token)    """

        payload = decode_jwt(token)

    if not payload:    

        return None    if not payload:

            return None

    return payload.get('ceo_id')    

    return payload.get('ceo_id')



def get_token_metadata(token: str) -> Optional[Dict[str, Any]]:

    """def get_token_metadata(token: str) -> Optional[Dict[str, Any]]:

    Extract full token metadata for logging and debugging.    """

        Extract full token metadata for logging and debugging.

    Args:    

        token (str): JWT token string    Args:

            token (str): JWT token string

    Returns:    

        Optional[Dict[str, Any]]: Token metadata including user_id, role, ceo_id, exp, jti    Returns:

    """        Optional[Dict[str, Any]]: Token metadata including user_id, role, ceo_id, exp, jti

    payload = decode_jwt(token)    """

        payload = decode_jwt(token)

    if not payload:    

        return None    if not payload:

            return None

    return {    

        'user_id': payload.get('sub'),    return {

        'role': payload.get('role'),        'user_id': payload.get('sub'),

        'ceo_id': payload.get('ceo_id'),        'role': payload.get('role'),

        'issued_at': payload.get('iat'),        'ceo_id': payload.get('ceo_id'),

        'expires_at': payload.get('exp'),        'issued_at': payload.get('iat'),

        'token_id': payload.get('jti'),        'expires_at': payload.get('exp'),

        'is_expired': payload.get('exp', 0) < int(time.time())        'token_id': payload.get('jti'),

    }        'is_expired': payload.get('exp', 0) < int(time.time())

    }



def create_jwt(
    user_id: str,
    role: str,
    ceo_id: Optional[str] = None,
    expires_minutes: Optional[int] = None
) -> str:
    """
    Generate a signed JWT with multi-tenant isolation support.
    
    Args:
        user_id (str): User identifier (buyer_id, vendor_id, or ceo_id)
        role (str): User role ('Buyer', 'Vendor', or 'CEO')
        ceo_id (str, optional): CEO identifier for multi-tenant isolation.
                                Required for Buyer and Vendor roles.
        expires_minutes (int, optional): Custom expiry time. If not provided,
                                         uses role-based default.
    
    Returns:
        str: Signed JWT token
    
    Raises:
        ValueError: If ceo_id is missing for Buyer/Vendor roles
    
    Example:
        >>> create_jwt('wa_1234567890', 'Buyer', ceo_id='ceo_abc123')
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    role_upper = role.upper()
    
    # Validate ceo_id requirement for multi-tenancy
    if role_upper in ['BUYER', 'VENDOR'] and not ceo_id:
        raise ValueError(f"{role} tokens require ceo_id for multi-tenant isolation")
    
    # Determine expiry time
    if expires_minutes is None:
        expires_minutes = TOKEN_EXPIRY_MINUTES.get(role_upper, 30)
    
    # Calculate timestamps
    now = int(time.time())
    exp_time = now + (expires_minutes * 60)
    
    # Build JWT payload
    payload = {
        'sub': user_id,           # Subject (user identifier)
        'role': role,             # User role for RBAC
        'iat': now,               # Issued at timestamp
        'exp': exp_time,          # Expiration timestamp
        'jti': secrets.token_hex(16)  # Unique token ID for revocation tracking
    }
    
    # Add ceo_id for multi-tenant isolation (except for CEO role)
    if ceo_id and role_upper != 'CEO':
        payload['ceo_id'] = ceo_id
    
    # Sign and return token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(
        f"JWT created: user_id={user_id}, role={role}, "
        f"ceo_id={ceo_id}, expires_in={expires_minutes}min, jti={payload['jti'][:8]}..."
    )
    
    return token


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token (str): JWT token string
    
    Returns:
        Optional[Dict[str, Any]]: Decoded payload with user info, or None if invalid
    
    Example:
        >>> payload = decode_jwt(token)
        >>> print(payload['sub'], payload['role'], payload.get('ceo_id'))
        'wa_1234567890' 'Buyer' 'ceo_abc123'
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        logger.debug(
            f"JWT decoded: user_id={payload.get('sub')}, "
            f"role={payload.get('role')}, jti={payload.get('jti', '')[:8]}..."
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT validation failed: Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        return None


def verify_token_role(token: str, required_role: str) -> Optional[str]:
    """
    Verify JWT token and check if it has the required role.
    
    Args:
        token (str): JWT token string
        required_role (str): Required role ('Buyer', 'Vendor', or 'CEO')
    
    Returns:
        Optional[str]: user_id if token is valid and has required role, None otherwise
    
    Example:
        >>> vendor_id = verify_token_role(token, 'Vendor')
        >>> if vendor_id:
        ...     # Proceed with vendor-specific logic
    """
    payload = decode_jwt(token)
    
    if not payload:
        return None
    
    if payload.get('role', '').upper() != required_role.upper():
        logger.warning(
            f"Role mismatch: expected {required_role}, got {payload.get('role')}"
        )
        return None
    
    return payload.get('sub')


def extract_ceo_id(token: str) -> Optional[str]:
    """
    Extract ceo_id from JWT token for multi-tenant operations.
    
    Args:
        token (str): JWT token string
    
    Returns:
        Optional[str]: ceo_id if present in token, None otherwise
    
    Note:
        CEO tokens don't include ceo_id (they ARE the CEO).
        Buyer and Vendor tokens must include ceo_id.
    """
    payload = decode_jwt(token)
    
    if not payload:
        return None
    
    return payload.get('ceo_id')


def get_token_metadata(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract full token metadata for logging and debugging.
    
    Args:
        token (str): JWT token string
    
    Returns:
        Optional[Dict[str, Any]]: Token metadata including user_id, role, ceo_id, exp, jti
    """
    payload = decode_jwt(token)
    
    if not payload:
        return None
    
    return {
        'user_id': payload.get('sub'),
        'role': payload.get('role'),
        'ceo_id': payload.get('ceo_id'),
        'issued_at': payload.get('iat'),
        'expires_at': payload.get('exp'),
        'token_id': payload.get('jti'),
        'is_expired': payload.get('exp', 0) < int(time.time())
    }

