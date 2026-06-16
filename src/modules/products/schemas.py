from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    product_code: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    price: float
    offer: Optional[int] = 0
    stock: int
    is_active: bool = True

class ProductCreate(ProductBase):
    category_id: int
    purchase_amount: Optional[float] = 0.0
    image_url: Optional[str] = None
    features: Optional[List[str]] = None
    specs: Optional[Dict[str, str]] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    purchase_amount: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    category_id: int
    image_url: Optional[str] = None
    created_at: datetime
    features: Optional[List[str]] = None
    specs: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True

class AdminProductResponse(ProductResponse):
    purchase_amount: float

    class Config:
        from_attributes = True

class PaginatedProductResponse(BaseModel):
    total: int
    page: int
    limit: int
    products: List[ProductResponse]
