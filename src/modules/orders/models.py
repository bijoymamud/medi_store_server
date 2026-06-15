from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, on_route, completed, cancelled
    payment_method = Column(String, default="sslcommerz", nullable=False)  # sslcommerz, cod
    payment_status = Column(String, default="pending", nullable=False)  # pending, paid, failed
    review_status = Column(String, default="requested", nullable=False)  # requested, submitted, verified, rejected
    review_text = Column(String, nullable=True)
    review_rating = Column(Integer, nullable=True)
    review_submitted_at = Column(DateTime(timezone=True), nullable=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def user_name(self) -> str:
        return self.user.full_name if self.user else ""

    @property
    def user_email(self) -> str:
        return self.user.email if self.user else ""

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Snapshotted price at checkout

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    @property
    def product_name(self) -> str:
        return self.product.name if self.product else "Unknown Product"

    @property
    def product_image(self) -> str:
        return self.product.image_url if (self.product and self.product.image_url) else ""
