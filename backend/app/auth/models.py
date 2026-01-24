"""
User model for authentication.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class User(Base):
    """
    User account table.
    Stores authentication credentials and profile information.
    """
    __tablename__ = "users"
    
    # UUID as string primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Email as unique identifier for login
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Hashed password (never store plain text!)
    hashed_password = Column(String, nullable=False)
    
    # User's display name
    full_name = Column(String, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Profile settings (JSON-like text for flexibility)
    preferences = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
