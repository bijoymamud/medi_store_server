from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TestimonialCreate(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    rating: int = Field(default=5, ge=1, le=5)
    image: Optional[str] = None

class TestimonialResponse(BaseModel):
    id: int
    name: str
    role: str
    content: str
    rating: int
    image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
