import os
import json
import time
import random
import string
import boto3
import logging
import jwt  # PyJWT library for JWT handling
from datetime import datetime, timedelta

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Retrieve table names from environment variables set by the SAM template
USERS_TABLE = os.environ.get('USERS_TABLE')
OTPS_TABLE = os.environ.get('OTPS_TABLE')
AUDIT_LOGS_TABLE = os.environ.get('AUDIT_LOGS_TABLE')
SECRET_KEY = os.environ.get('JWT_SECRET', 'temporary_dev_secret')  # For JWT signing in a real app

# Zero Trust Security Constants
# OTPs expire after 5 minutes (300 seconds)
OTP_TTL_SECONDS = 300
# OTP length for general users (Buyer/Vendor) - 8 characters alphanumeric + special chars
OTP_LENGTH_DEFAULT = 8
# OTP length for CEO (simulated 2FA) - 6 digits + symbols
OTP_LENGTH_CEO = 6

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def _response(status, message, data=None):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": message, **(data or {})})
    }

def _generate_otp(role):
    """Generates a random, single-use OTP based on the user's role."""
    if role == 'CEO':
        # CEO OTP is 6 characters: digits + symbols, as required for high-value approvals.
        CEO_CHARS = string.digits + string.punctuation
        return ''.join(random.choices(CEO_CHARS, k=OTP_LENGTH_CEO))
    else:
        # Default OTP is 8 characters: alphanumeric + special characters.
        DEFAULT_CHARS = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choices(DEFAULT_CHARS, k=OTP_LENGTH_DEFAULT))

def _log_event(user_id, action, status, message=None, meta=None):
    """
    Records an immutable event in the AuditLogs table.
    (Zero Trust - Assume Breach)
    """
    if not AUDIT_LOGS_TABLE:
        print("Warning: AUDIT_LOGS_TABLE not set.")
        return

    audit_table = dynamodb.Table(AUDIT_LOGS_TABLE)
    try:
        audit_table.put_item(
            Item={
                'log_id': f'{user_id}-{int(time.time())}',  # Using user_id as Partition Key
                'timestamp': int(time.time()),
                'user_id': user_id,
                'action': action,
                'status': status,
                'message': message or 'N/A',
                'meta': meta or {}
            }
        )
    except Exception as e:
        print(f"ERROR logging event to AuditLogs: {e}")

# Placeholder for JWT generation (not fully implemented)
def _generate_jwt(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=10)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def request_otp(event, context):
    """
    API Handler: Initiates the OTP process for a user.
    1. Finds user.
    2. Generates OTP based on role.
    3. Stores OTP in the secure, TTL-enabled table.
    4. Simulates sending the OTP.
    5. Logs the action.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        
        if not user_id or not USERS_TABLE or not OTPS_TABLE:
            _log_event(user_id, 'OTP_REQUEST', 'FAILED', 'Missing user_id or ENV variables.')
            return {'statusCode': 400, 'body': json.dumps({'message': 'Missing user identifier or configuration.'})}

        users_table = dynamodb.Table(USERS_TABLE)
        
        # 1. Find User to get their role and contact info
        user_response = users_table.get_item(Key={'user_id': user_id})
        user_item = user_response.get('Item')
        
        if not user_item:
            _log_event(user_id, 'OTP_REQUEST', 'FAILED', 'User not found.')
            return {'statusCode': 404, 'body': json.dumps({'message': 'User not found.'})}

        role = user_item.get('role', 'Buyer') # Default to Buyer if not specified
        contact_info = user_item.get('contact', 'Email/Phone') # Placeholder contact

        # 2. Generate and Store OTP (Zero Trust - Verify Explicitly)
        otp_code = _generate_otp(role)
        
        # Calculate expiration time as a Unix timestamp (seconds since epoch)
        expires_at_timestamp = int(time.time()) + OTP_TTL_SECONDS
        
        otps_table = dynamodb.Table(OTPS_TABLE)
        otps_table.put_item(
            Item={
                'user_id': user_id,
                'otp_code': otp_code,
                'role': role,
                'expires_at': expires_at_timestamp # DynamoDB automatically deletes this item after this time
            }
        )

        # 4. Simulate OTP Delivery (In a real app, this would use SNS/SES/Messaging APIs)
        print(f"SUCCESS: Simulating delivery of OTP {otp_code} to {contact_info} for user {user_id}")

        # 5. Log the action
        _log_event(user_id, 'OTP_REQUEST', 'SUCCESS', f'OTP generated and stored with TTL {OTP_TTL_SECONDS}s.')

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'OTP requested for {user_id}. Check your {contact_info}.',
                'ttl_seconds': OTP_TTL_SECONDS
            })
        }

    except Exception as e:
        logger.error(f"Error during OTP request: {e}")
        _log_event(user_id if 'user_id' in locals() else 'unknown', "OTP_REQUEST", "ERROR", str(e))
        return _response(500, "Internal error during OTP request.")


def verify_otp(event, context):
    """
    API Handler: Verifies the submitted OTP against the time-sensitive table.
    1. Retrieves the OTP record from the table.
    2. Checks if the submitted code matches the stored code.
    3. Deletes the used OTP record instantly upon success.
    4. Logs the action.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        submitted_otp = body.get('otp_code')

        if not user_id or not submitted_otp or not OTPS_TABLE:
            _log_event(user_id, 'OTP_VERIFY', 'FAILED', 'Missing user_id or OTP code.')
            return {'statusCode': 400, 'body': json.dumps({'message': 'Missing required fields.'})}

        otps_table = dynamodb.Table(OTPS_TABLE)
        
        # 1. Retrieve the OTP record
        otp_response = otps_table.get_item(Key={'user_id': user_id})
        otp_item = otp_response.get('Item')

        if not otp_item:
            # If item is not found, it's either expired (deleted by TTL) or never requested.
            _log_event(user_id, 'OTP_VERIFY', 'FAILED', 'OTP expired or not found.')
            return {'statusCode': 401, 'body': json.dumps({'message': 'Invalid or expired OTP.'})}

        # 2. Check for match
        if submitted_otp == otp_item['otp_code']:
            
            # 3. Success: Delete the used OTP record instantly
            otps_table.delete_item(Key={'user_id': user_id})
            token = _generate_jwt(user_id, otp_item['role'])
            # TODO: Placeholder for JWT Generation (short-lived access token)
            # In a real app, a JWT containing the user's role would be generated and returned here.
            
            _log_event(user_id, 'OTP_VERIFY', 'SUCCESS', 'Authentication successful. JWT issued.')
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Authentication successful. Welcome!',
                    'role': otp_item['role'],
                    'token': token  # Placeholder, would be a real JWT in a full implementation 
                })
            }
        else:
            _log_event(user_id, 'OTP_VERIFY', 'FAILED', 'OTP mismatch.')
            return {'statusCode': 401, 'body': json.dumps({'message': 'Invalid OTP.'})}

    except Exception as e:
        logger.error(f"Error during OTP verification: {e}")
        _log_event(user_id if 'user_id' in locals() else 'unknown', "OTP_VERIFY", "ERROR", str(e))
        return _response(500, "Internal error during OTP verification.")

def lambda_handler(event, context):
    """
    Main Lambda entry point. Routes requests based on the API path.
    """
    path = event.get('path')
    method = event.get('httpMethod')

    if path == '/auth/request' and method == 'POST':
        return request_otp(event, context)
    
    if path == '/auth/verify' and method == 'POST':
        return verify_otp(event, context)
        
    return {
        'statusCode': 404,
        'body': json.dumps({'message': 'Not Found'})
    }
