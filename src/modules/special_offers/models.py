from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base

class SpecialOffer(Base):
    __tablename__ = "special_offers"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    selling_prize = Column(Float, nullable=False)
    discount_prize = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    product_image = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category")
    product = relationship("Product")
