from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from src.database.connection import Base

class SpecialOffer(Base):
    __tablename__ = "special_offers"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    selling_prize = Column(Float, nullable=False)
    discount_prize = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    product_image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
