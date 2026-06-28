from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpecialOfferBase(BaseModel):
    product_name: str
    selling_prize: float
    discount_prize: Optional[float] = None
    discount_amount: Optional[float] = None
    category_id: Optional[int] = None
    product_id: Optional[int] = None

class SpecialOfferCreate(SpecialOfferBase):
    pass

class SpecialOfferUpdate(BaseModel):
    product_name: Optional[str] = None
    selling_prize: Optional[float] = None
    discount_prize: Optional[float] = None
    discount_amount: Optional[float] = None
    category_id: Optional[int] = None
    product_id: Optional[int] = None

class SpecialOfferResponse(SpecialOfferBase):
    id: int
    product_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
