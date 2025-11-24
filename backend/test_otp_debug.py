import sys
import os
sys.path.append(os.getcwd())

from common.config import settings
from auth_service.otp_manager import _send_sms, _send_email

print(f"Current Environment: {settings.ENVIRONMENT}")
print("Attempting to send SMS...")
try:
    _send_sms("+2348000000000", "Test OTP: 123456")
except Exception as e:
    print(f"SMS Error: {e}")

print("Attempting to send Email...")
try:
    _send_email("test@example.com", "Test Subject", "Test Body")
except Exception as e:
    print(f"Email Error: {e}")
