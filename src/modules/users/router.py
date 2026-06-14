from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from pydantic import BaseModel
from src.utils.dependencies import get_admin_user
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.modules.users import models, schemas
from passlib.context import CryptContext
from typing import Optional
import os
import shutil

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

from datetime import datetime, timedelta, timezone
from src.utils.email_sender import generate_otp, send_otp_email

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(password)
    otp = generate_otp()
    
    # Optional image saving logic could go here
    # For now, just construct full_name
    full_name = f"{first_name} {last_name}"
    
    new_user = models.User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        phone=phone,
        address=address,
        is_active=False,
        is_verified=False,
        otp_code=otp,
        otp_expiry=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    send_otp_email(new_user.email, otp)
    
    return new_user

@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

class PromoteRequest(BaseModel):
    email: str

@router.post("/promote")
def promote_user(
    payload: PromoteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_admin_user)
):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    db.commit()
    return {"message": f"{user.email} has been promoted to admin"}
