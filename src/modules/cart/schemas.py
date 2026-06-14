from pydantic import BaseModel
from typing import List, Optional

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    quantity: int
    subtotal: float

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_price: float
