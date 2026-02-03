"""
Test database models and operations.
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import Document, ChatAudit


class TestDocumentModel:
    """Test Document model."""
    
    def test_create_document(self, db: Session):
        """Test creating a document."""
        doc = Document(
            id="test-doc-1",
            filename="test.pdf",
            content_type="application/pdf",
            preview_text="This is a test document"
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        assert doc.id == "test-doc-1"
        assert doc.filename == "test.pdf"
        assert doc.content_type == "application/pdf"
        assert doc.preview_text == "This is a test document"
        assert isinstance(doc.created_at, datetime)
    
    def test_query_documents(self, db: Session):
        """Test querying documents."""
        # Create multiple documents
        doc1 = Document(id="doc-1", filename="file1.pdf", content_type="application/pdf")
        doc2 = Document(id="doc-2", filename="file2.txt", content_type="text/plain")
        
        db.add_all([doc1, doc2])
        db.commit()
        
        # Query all documents
        documents = db.query(Document).all()
        assert len(documents) == 2
        
        # Query by filename
        result = db.query(Document).filter(Document.filename == "file1.pdf").first()
        assert result.id == "doc-1"
    
    def test_document_default_values(self, db: Session):
        """Test document with default values."""
        doc = Document(
            id="doc-3",
            filename="minimal.txt",
            content_type="text/plain"
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        assert doc.preview_text is None
        assert doc.created_at is not None


class TestChatAuditModel:
    """Test ChatAudit model."""
    
    def test_create_chat_audit(self, db: Session):
        """Test creating a chat audit entry."""
        audit = ChatAudit(
            id="audit-1",
            user_id="user-123",
            provider="ollama",
            model="llama3.1",
            question="What is the policy?",
            answer="The policy states...",
            cited_doc_ids=["doc-1", "doc-2"]
        )
        
        db.add(audit)
        db.commit()
        db.refresh(audit)
        
        assert audit.id == "audit-1"
        assert audit.user_id == "user-123"
        assert audit.provider == "ollama"
        assert audit.model == "llama3.1"
        assert audit.question == "What is the policy?"
        assert audit.answer == "The policy states..."
        assert audit.cited_doc_ids == ["doc-1", "doc-2"]
        assert isinstance(audit.created_at, datetime)
    
    def test_chat_audit_without_citations(self, db: Session):
        """Test chat audit without citations."""
        audit = ChatAudit(
            id="audit-2",
            user_id="user-456",
            provider="openai",
            model="gpt-4",
            question="Test question",
            answer="Test answer"
        )
        
        db.add(audit)
        db.commit()
        db.refresh(audit)
        
        assert audit.cited_doc_ids is None
    
    def test_query_audits_by_user(self, db: Session):
        """Test querying audits by user."""
        audit1 = ChatAudit(
            id="audit-3",
            user_id="user-1",
            provider="ollama",
            model="llama3.1",
            question="Q1",
            answer="A1"
        )
        audit2 = ChatAudit(
            id="audit-4",
            user_id="user-1",
            provider="openai",
            model="gpt-4",
            question="Q2",
            answer="A2"
        )
        audit3 = ChatAudit(
            id="audit-5",
            user_id="user-2",
            provider="ollama",
            model="llama3.1",
            question="Q3",
            answer="A3"
        )
        
        db.add_all([audit1, audit2, audit3])
        db.commit()
        
        # Query by user
        user1_audits = db.query(ChatAudit).filter(ChatAudit.user_id == "user-1").all()
        assert len(user1_audits) == 2
        
        # Query by provider
        ollama_audits = db.query(ChatAudit).filter(ChatAudit.provider == "ollama").all()
        assert len(ollama_audits) == 2
