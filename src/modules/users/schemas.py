from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True
