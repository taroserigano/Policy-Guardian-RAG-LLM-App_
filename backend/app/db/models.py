"""
SQLAlchemy ORM models for PostgreSQL database.
Stores document metadata and chat audit logs.
"""
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class Document(Base):
    """
    Document metadata table.
    Stores information about uploaded documents.
    The actual vectors are stored in Pinecone.
    """
    __tablename__ = "documents"
    
    # UUID as string primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Original filename
    filename = Column(String, nullable=False, index=True)
    
    # MIME type (application/pdf, text/plain, etc.)
    content_type = Column(String, nullable=False)
    
    # Preview text (first 500 chars) for UI display
    preview_text = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class ChatAudit(Base):
    """
    Chat audit log table.
    Records every question/answer pair for compliance and analysis.
    """
    __tablename__ = "chat_audits"
    
    # UUID as string primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User identifier (can be session ID or user ID)
    user_id = Column(String, nullable=False, index=True)
    
    # LLM provider used (ollama, openai, anthropic)
    provider = Column(String, nullable=False)
    
    # Specific model name
    model = Column(String, nullable=False)
    
    # User question
    question = Column(Text, nullable=False)
    
    # AI-generated answer
    answer = Column(Text, nullable=False)
    
    # Array of cited document IDs (stored as JSON for SQLite compatibility)
    cited_doc_ids = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ChatAudit(id={self.id}, user_id={self.user_id}, provider={self.provider})>"
