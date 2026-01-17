"""
Database Models and Persistence Layer
SQLite-based storage for documents and chat history
"""
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, joinedload
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Document(Base):
    """Document metadata storage."""
    __tablename__ = "documents"
    
    id = Column(String(100), primary_key=True)
    filename = Column(String(500), nullable=False)
    content_type = Column(String(100), default="text/plain")
    content = Column(Text, nullable=True)  # Store raw content
    preview_text = Column(Text, nullable=True)
    size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)  # JSON string for extra metadata
    
    # Relationship to chat messages that reference this document
    citations = relationship("Citation", back_populates="document")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "content_type": self.content_type,
            "preview_text": self.preview_text,
            "size": self.size,
            "chunk_count": self.chunk_count,
            "is_indexed": self.is_indexed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_extra_metadata(self) -> Dict[str, Any]:
        """Get extra metadata as dict."""
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}
    
    def set_extra_metadata(self, value: Dict[str, Any]):
        """Set metadata from dict."""
        self.metadata_json = json.dumps(value) if value else None


class ChatMessage(Base):
    """Chat message storage."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    provider = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to citations
    citations = relationship("Citation", back_populates="chat_message")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "citations": [c.to_dict() for c in self.citations] if self.citations else []
        }


class Citation(Base):
    """Citation linking chat messages to document sources."""
    __tablename__ = "citations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    document_id = Column(String(100), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    text_preview = Column(Text, nullable=True)
    
    # Relationships
    chat_message = relationship("ChatMessage", back_populates="citations")
    document = relationship("Document", back_populates="citations")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.document_id,
            "filename": self.document.filename if self.document else "unknown",
            "chunk_index": self.chunk_index,
            "score": self.score,
            "text": self.text_preview
        }


class DatabaseManager:
    """Database session and operations manager."""
    
    def __init__(self, database_url: str = "sqlite:///./data/policy_rag.db"):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        
        # Ensure data directory exists
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine with appropriate settings for SQLite
        if "sqlite" in database_url:
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(database_url)
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        print(f"[OK] Database initialized: {database_url}")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    # Document operations
    def create_document(
        self,
        doc_id: str,
        filename: str,
        content: str,
        content_type: str = "text/plain",
        metadata: Optional[Dict] = None
    ) -> Document:
        """Create a new document record."""
        session = self.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename=filename,
                content=content,
                content_type=content_type,
                preview_text=content[:500] if content else "",
                size=len(content) if content else 0
            )
            if metadata:
                doc.metadata = metadata
            
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc
        finally:
            session.close()
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        session = self.get_session()
        try:
            return session.query(Document).filter(Document.id == doc_id).first()
        finally:
            session.close()
    
    def get_all_documents(self) -> List[Document]:
        """Get all documents."""
        session = self.get_session()
        try:
            return session.query(Document).order_by(Document.created_at.desc()).all()
        finally:
            session.close()
    
    def update_document_indexed(self, doc_id: str, chunk_count: int) -> bool:
        """Mark document as indexed."""
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.is_indexed = True
                doc.chunk_count = chunk_count
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its citations."""
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                # Delete citations referencing this document
                session.query(Citation).filter(Citation.document_id == doc_id).delete()
                session.delete(doc)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # Chat operations
    def save_chat_message(
        self,
        user_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        citations: Optional[List[Dict]] = None
    ) -> ChatMessage:
        """Save a chat message."""
        session = self.get_session()
        try:
            message = ChatMessage(
                user_id=user_id,
                role=role,
                content=content,
                provider=provider,
                model=model
            )
            session.add(message)
            session.flush()  # Get the message ID
            
            # Add citations if provided
            if citations:
                for cit in citations:
                    citation = Citation(
                        chat_message_id=message.id,
                        document_id=cit.get("doc_id"),
                        chunk_index=cit.get("chunk_index", 0),
                        score=cit.get("score", 0.0),
                        text_preview=cit.get("text", "")[:500]
                    )
                    session.add(citation)
            
            session.commit()
            session.refresh(message)
            return message
        finally:
            session.close()
    
    def get_chat_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[ChatMessage]:
        """Get chat history for a user."""
        session = self.get_session()
        try:
            messages = session.query(ChatMessage)\
                .options(
                    joinedload(ChatMessage.citations).joinedload(Citation.document)
                )\
                .filter(ChatMessage.user_id == user_id)\
                .order_by(ChatMessage.created_at.desc())\
                .limit(limit)\
                .all()
            # Make a copy of the data before closing session
            # by accessing the citations attribute while in session
            for msg in messages:
                for citation in msg.citations:
                    _ = citation.document  # Force load
            return messages[::-1]  # Reverse to get chronological order
        finally:
            session.close()
    
    def clear_chat_history(self, user_id: str) -> int:
        """Clear chat history for a user."""
        session = self.get_session()
        try:
            count = session.query(ChatMessage)\
                .filter(ChatMessage.user_id == user_id)\
                .delete()
            session.commit()
            return count
        finally:
            session.close()
    
    # Statistics
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self.get_session()
        try:
            return {
                "total_documents": session.query(Document).count(),
                "indexed_documents": session.query(Document).filter(Document.is_indexed == True).count(),
                "total_messages": session.query(ChatMessage).count(),
                "unique_users": session.query(ChatMessage.user_id).distinct().count()
            }
        finally:
            session.close()


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_database(database_url: str = "sqlite:///./data/policy_rag.db") -> DatabaseManager:
    """Get or create the global database manager."""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url=database_url)
    
    return _db_manager


# Testing
if __name__ == "__main__":
    print("="*60)
    print("Database Test")
    print("="*60)
    
    # Initialize database
    db = get_database("sqlite:///./data/test_db.db")
    
    # Create a document
    doc = db.create_document(
        doc_id="test-doc-1",
        filename="test_policy.txt",
        content="This is a test policy document with important information.",
        content_type="text/plain",
        metadata={"category": "HR", "version": "1.0"}
    )
    print(f"\nCreated document: {doc.filename}")
    
    # Mark as indexed
    db.update_document_indexed("test-doc-1", chunk_count=5)
    print("Document marked as indexed")
    
    # Save chat messages
    user_msg = db.save_chat_message(
        user_id="user-123",
        role="user",
        content="What is the leave policy?"
    )
    print(f"\nSaved user message: {user_msg.id}")
    
    assistant_msg = db.save_chat_message(
        user_id="user-123",
        role="assistant",
        content="The leave policy allows 20 days of annual leave.",
        provider="ollama",
        model="llama3.1:8b",
        citations=[{
            "doc_id": "test-doc-1",
            "chunk_index": 0,
            "score": 0.85,
            "text": "Annual leave: 20 days per year..."
        }]
    )
    print(f"Saved assistant message: {assistant_msg.id}")
    
    # Get chat history
    history = db.get_chat_history("user-123")
    print(f"\nChat history ({len(history)} messages):")
    for msg in history:
        print(f"  [{msg.role}]: {msg.content[:50]}...")
    
    # Get stats
    stats = db.get_stats()
    print(f"\nDatabase stats: {stats}")
    
    # List documents
    docs = db.get_all_documents()
    print(f"\nAll documents ({len(docs)}):")
    for d in docs:
        print(f"  - {d.filename} (indexed: {d.is_indexed})")
