from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from auth_logic import register_user, login_user, verify_otp_code
from utils import format_response, validate_email, validate_phone_number, validate_user_name

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str
    name: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    validate_email(req.email)
    validate_phone_number(req.phone)
    validate_user_name(req.name)
    user_id = register_user(req.email, req.phone, req.name)
    return format_response("success", "User registered", {"user_id": user_id})

class LoginRequest(BaseModel):
    user_id: str

@router.post("/login")
def login(req: LoginRequest):
    try:
        login_user(req.user_id)
        return format_response("success", "OTP sent")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class VerifyRequest(BaseModel):
    user_id: str
    otp: str

@router.post("/verify-otp")
def verify(req: VerifyRequest):
    try:
        token = verify_otp_code(req.user_id, req.otp)
        return format_response("success", "OTP verified", {"token": token})
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
