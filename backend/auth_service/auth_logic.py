from otp_manager import generate_otp, send_otp, validate_otp

_users_db = {}  # Dummy placeholder for actual DB calls

def register_user(email, phone, name):
    # Simulate unique user_id creation and persist user info
    user_id = f"user-{len(_users_db) + 1}"
    _users_db[user_id] = {"email": email, "phone": phone, "name": name}
    return user_id

def login_user(user_id):
    # Generate and send OTP
    if user_id not in _users_db:
        raise Exception("User not found")
    otp = generate_otp(user_id)
    send_otp(_users_db[user_id]["phone"], otp)
    return True

def verify_otp(user_id, otp):
    # Validate OTP correctness
    return validate_otp(user_id, otp)
