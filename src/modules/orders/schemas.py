from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CheckoutRequest(BaseModel):
    shipping_address: str
    phone: str
    payment_method: str = Field(..., pattern="^(sslcommerz|cod|cod_prepaid)$")
    prepaid_method: Optional[str] = None
    prepaid_number: Optional[str] = None
    prepaid_txid: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    product_image: Optional[str] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    total_amount: float
    shipping_address: str
    phone: str
    status: str
    payment_method: str
    payment_status: str
    review_status: str
    review_text: Optional[str] = None
    review_rating: Optional[int] = None
    review_submitted_at: Optional[datetime] = None
    transaction_id: str
    prepaid_method: Optional[str] = None
    prepaid_number: Optional[str] = None
    prepaid_txid: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse]
    payment_url: Optional[str] = None    # SSLCommerz redirect URL

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(on_route|completed|cancelled)$")

class ReviewSubmitRequest(BaseModel):
    review_text: str
    review_rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewVerifyRequest(BaseModel):
    is_valid: bool
