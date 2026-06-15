from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from src.database.connection import get_db
from src.modules.users.models import User
from src.modules.users.router import pwd_context, get_password_hash
from src.modules.auth import schemas
from src.utils.jwt_handler import create_access_token
from src.utils.email_sender import generate_otp, send_otp_email

router = APIRouter()

@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    if user.email in ["webdev.bijoy@gmail.com", "bijoymamud.09@gmail.com"] and not user.is_admin:
        user.is_admin = True
        db.commit()
        db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(days=7))
    
    return {
        "message": "Login successful",
        "tokens": {
            "access": access_token,
            "refresh": refresh_token
        },
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin
        }
    }

@router.post("/verify-email")
def verify_email(payload: schemas.VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp_code or user.otp_code != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    if user.otp_expiry and user.otp_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
        
    user.is_verified = True
    user.is_active = True
    # We leave otp_code and otp_expiry intact so the password reset flow can consume it
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # We don't want to leak if a user exists or not, but for simplicity we can return success
        return {"message": "If that email is registered, an OTP has been sent."}
        
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    
    send_otp_email(user.email, otp)
    return {"message": "If that email is registered, an OTP has been sent."}

@router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.otp_code or user.otp_code != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    if user.otp_expiry and user.otp_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
        
    user.hashed_password = get_password_hash(payload.new_password)
    user.otp_code = None
    user.otp_expiry = None
    db.commit()
    
    return {"message": "Password reset successfully"}
