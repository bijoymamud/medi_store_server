from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from src.database.connection import get_db
from src.modules.users.models import User
from src.modules.users.router import pwd_context, get_password_hash
from src.modules.auth import schemas
from src.utils.jwt_handler import create_access_token, decode_access_token
from src.utils.email_sender import generate_otp, send_otp_email
from src.utils.rate_limit import RateLimiter

router = APIRouter()

login_limiter = RateLimiter(limit=10, window=60)
forgot_password_limiter = RateLimiter(limit=5, window=60)

@router.post("/login", response_model=schemas.TokenResponse, dependencies=[Depends(login_limiter)])
def login(payload: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(days=7))
    
    # Set the refresh token as a secure HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/",
    )
    
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

@router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
        
    payload = decode_access_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
        
    email: str = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
        
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
        
    # Rotate access token
    new_access_token = create_access_token(data={"sub": user.email})
    
    # Rotate refresh token
    new_refresh_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(days=7))
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    
    return {
        "tokens": {
            "access": new_access_token,
            "refresh": new_refresh_token
        }
    }

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )
    return {"message": "Logged out successfully"}

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

@router.post("/forgot-password", dependencies=[Depends(forgot_password_limiter)])
def forgot_password(
    payload: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # We don't want to leak if a user exists or not, but for simplicity we can return success
        return {"message": "If that email is registered, an OTP has been sent."}
        
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    
    background_tasks.add_task(send_otp_email, user.email, otp)
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
