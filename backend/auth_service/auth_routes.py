from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from auth_logic import register_user, login_user, verify_otp

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str
    name: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    try:
        user_id = register_user(request.email, request.phone, request.name)
        return {"message": "User registered successfully", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class LoginRequest(BaseModel):
    user_id: str

@router.post("/login")
async def login(request: LoginRequest):
    try:
        otp_sent = login_user(request.user_id)
        return {"message": "OTP sent", "otp_sent": otp_sent}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class OTPVerifyRequest(BaseModel):
    user_id: str
    otp: str

@router.post("/verify-otp")
async def verify_otp_route(request: OTPVerifyRequest):
    try:
        verified = verify_otp(request.user_id, request.otp)
        if verified:
            return {"message": "OTP verified successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid OTP or expired")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
