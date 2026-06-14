from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from src.database.connection import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    product_code = Column(String, unique=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    short_description = Column(String, nullable=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    offer = Column(Integer, default=0)
    stock = Column(Integer, default=0)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    features = Column(JSON, nullable=True)
    specs = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    category = relationship("Category", back_populates="products")
