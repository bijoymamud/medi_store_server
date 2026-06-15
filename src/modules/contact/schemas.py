from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class ContactRequestCreate(BaseModel):
    client_name: str
    email: EmailStr
    department: str
    specifications: str

class ContactRequestResponse(BaseModel):
    id: int
    client_name: str
    email: EmailStr
    department: str
    specifications: str
    created_at: datetime

    class Config:
        from_attributes = True
