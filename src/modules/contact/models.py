from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from src.database.connection import Base

class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    department = Column(String, nullable=False)
    specifications = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
