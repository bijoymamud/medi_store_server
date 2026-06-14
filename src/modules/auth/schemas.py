from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

from typing import Any

class Tokens(BaseModel):
    access: str
    refresh: str

class TokenResponse(BaseModel):
    message: str
    tokens: Tokens
    user: Any

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
