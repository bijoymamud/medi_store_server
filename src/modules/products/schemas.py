from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    is_active: bool = True

class ProductCreate(ProductBase):
    category_id: int
    image_url: Optional[str] = None
    features: Optional[List[str]] = None
    specs: Optional[Dict[str, str]] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    category_id: int
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
