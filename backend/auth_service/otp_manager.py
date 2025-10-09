import random
import string
from datetime import datetime, timedelta

_otp_store = {}  # Dict storing user_id -> (otp, expiry)

# Functions to generate, send, and validate OTPs
def generate_otp(user_id, length=8):
    otp = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    expiry = datetime.utcnow() + timedelta(minutes=5)
    _otp_store[user_id] = (otp, expiry)
    return otp

def send_otp(phone_number, otp):
    # Stub for sending OTP via SMS/WhatsApp/Instagram APIs
    print(f"Sending OTP {otp} to phone {phone_number}")

def validate_otp(user_id, otp_provided):
    if user_id not in _otp_store:
        return False
    otp, expiry = _otp_store[user_id]
    if datetime.utcnow() > expiry:
        del _otp_store[user_id]
        return False
    if otp == otp_provided:
        del _otp_store[user_id]
        return True
    return False
