import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from src.database.connection import get_db
from src.utils.dependencies import get_current_user
from src.modules.users.models import User

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/profile/")
def get_profile(current_user: User = Depends(get_current_user)):
    parts = (current_user.full_name or "").split(" ", 1)
    first_name = parts[0] if len(parts) > 0 else ""
    last_name = parts[1] if len(parts) > 1 else ""
    
    backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
    full_image_url = None
    if getattr(current_user, "image", None):
        full_image_url = f"{backend_url}{current_user.image}" if not current_user.image.startswith("http") else current_user.image

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "address": current_user.address,
            "image": full_image_url,
            "is_active": current_user.is_active,
            "is_admin": current_user.is_admin,
        }
    }

@router.patch("/profile/update/")
async def update_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content_type = request.headers.get("content-type", "")
    
    first_name = None
    last_name = None
    phone = None
    address = None
    image_path = None
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        if "image" in form:
            upload_file = form["image"]
            if isinstance(upload_file, UploadFile) and upload_file.filename:
                os.makedirs("uploads/profiles", exist_ok=True)
                file_ext = os.path.splitext(upload_file.filename)[1]
                filename = f"user_{current_user.id}_{int(datetime.now().timestamp())}{file_ext}"
                file_path = f"uploads/profiles/{filename}"
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(upload_file.file, buffer)
                image_path = f"/uploads/profiles/{filename}"
        
        if "first_name" in form:
            first_name = str(form.get("first_name"))
        if "last_name" in form:
            last_name = str(form.get("last_name"))
        if "phone" in form:
            phone = str(form.get("phone"))
        if "address" in form:
            address = str(form.get("address"))
    else:
        try:
            body = await request.json()
            first_name = body.get("first_name")
            last_name = body.get("last_name")
            phone = body.get("phone")
            address = body.get("address")
        except Exception:
            pass
            
    # Update full_name if first_name or last_name changed
    if first_name is not None or last_name is not None:
        parts = (current_user.full_name or "").split(" ", 1)
        curr_first = parts[0] if len(parts) > 0 else ""
        curr_last = parts[1] if len(parts) > 1 else ""
        
        f_name = first_name if first_name is not None else curr_first
        l_name = last_name if last_name is not None else curr_last
        current_user.full_name = f"{f_name} {l_name}".strip()
        
    if phone is not None:
        current_user.phone = phone
    if address is not None:
        current_user.address = address
    if image_path is not None:
        current_user.image = image_path
        
    db.commit()
    db.refresh(current_user)
    
    parts = (current_user.full_name or "").split(" ", 1)
    f_name = parts[0] if len(parts) > 0 else ""
    l_name = parts[1] if len(parts) > 1 else ""
    
    backend_url = os.getenv("BACKEND_URL", "http://localhost:5000")
    full_image_url = None
    if getattr(current_user, "image", None):
        full_image_url = f"{backend_url}{current_user.image}" if not current_user.image.startswith("http") else current_user.image
        
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": f_name,
            "last_name": l_name,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "address": current_user.address,
            "image": full_image_url,
            "is_active": current_user.is_active,
            "is_admin": current_user.is_admin,
        }
    }

@router.post("/change-password/")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not pwd_context.verify(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    current_user.hashed_password = pwd_context.hash(payload.new_password)
    db.commit()
    return {"status": "success", "message": "Password changed successfully"}
