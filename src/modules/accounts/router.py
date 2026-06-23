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
            uploaded_image = form["image"]
            print(f"[UPLOAD DEBUG] Got image field. Type: {type(uploaded_image)}, filename: {getattr(uploaded_image, 'filename', 'N/A')}")
            if isinstance(uploaded_image, UploadFile) and uploaded_image.filename:
                try:
                    # Read all bytes from the async UploadFile
                    file_bytes = await uploaded_image.read()
                    print(f"[UPLOAD DEBUG] Read {len(file_bytes)} bytes from upload")
                    
                    if len(file_bytes) > 0:
                        import uuid as uuid_mod
                        file_ext = os.path.splitext(uploaded_image.filename)[1] or ".jpg"
                        unique_filename = f"{uuid_mod.uuid4().hex}{file_ext}"
                        upload_dir = os.path.join(os.getcwd(), "uploads", "profiles")
                        os.makedirs(upload_dir, exist_ok=True)
                        file_path = os.path.join(upload_dir, unique_filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(file_bytes)
                        
                        saved_size = os.path.getsize(file_path)
                        print(f"[UPLOAD DEBUG] Saved to {file_path}, size: {saved_size} bytes")
                        
                        if saved_size > 0:
                            image_path = f"/uploads/profiles/{unique_filename}"
                            print(f"[UPLOAD DEBUG] image_path set to: {image_path}")
                        else:
                            print(f"[UPLOAD DEBUG] ERROR: File saved but size is 0!")
                    else:
                        print(f"[UPLOAD DEBUG] ERROR: Read 0 bytes - file is empty!")
                        
                except Exception as e:
                    print(f"[UPLOAD DEBUG] EXCEPTION during upload: {type(e).__name__}: {e}")
            else:
                print(f"[UPLOAD DEBUG] Skipped - not UploadFile or no filename")
        else:
            print(f"[UPLOAD DEBUG] 'image' key not in form. Form keys: {list(form.keys())}")
        
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
    # Only update image if upload actually succeeded (non-empty path)
    if image_path:
        current_user.image = image_path
        print(f"[UPLOAD DEBUG] Saving image path to DB: {image_path}")
        
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
