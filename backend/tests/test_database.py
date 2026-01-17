"""
Comprehensive Test Suite for Database Module
Tests SQLite persistence, models, and database operations
"""
import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import (
    Document, ChatMessage, Citation,
    DatabaseManager, get_database
)


class TestDocumentModel:
    """Test Document model."""
    
    def test_document_to_dict(self):
        """Test Document to_dict method."""
        doc = Document(
            id="test-doc-1",
            filename="test.txt",
            content_type="text/plain",
            content="Test content",
            size=12,
            chunk_count=2,
            is_indexed=True
        )
        
        result = doc.to_dict()
        
        assert result["id"] == "test-doc-1"
        assert result["filename"] == "test.txt"
        assert result["content_type"] == "text/plain"
        assert result["size"] == 12
        assert result["chunk_count"] == 2
        assert result["is_indexed"] is True
    
    def test_document_metadata_methods(self):
        """Test Document metadata get/set methods."""
        doc = Document(
            id="meta-doc",
            filename="meta.txt"
        )
        
        # Set metadata
        doc.set_extra_metadata({"key": "value", "number": 42})
        
        # Get metadata
        meta = doc.get_extra_metadata()
        
        assert meta["key"] == "value"
        assert meta["number"] == 42
    
    def test_document_empty_metadata(self):
        """Test Document with no metadata."""
        doc = Document(
            id="empty-meta",
            filename="empty.txt"
        )
        
        meta = doc.get_extra_metadata()
        assert meta == {}


class TestChatMessageModel:
    """Test ChatMessage model."""
    
    def test_chat_message_to_dict(self):
        """Test ChatMessage to_dict method."""
        msg = ChatMessage(
            id=1,
            user_id="user-123",
            role="user",
            content="Hello, world!",
            provider="ollama",
            model="llama3.1:8b"
        )
        
        result = msg.to_dict()
        
        assert result["id"] == 1
        assert result["user_id"] == "user-123"
        assert result["role"] == "user"
        assert result["content"] == "Hello, world!"
        assert result["provider"] == "ollama"
        assert result["model"] == "llama3.1:8b"


class TestCitationModel:
    """Test Citation model."""
    
    def test_citation_to_dict(self):
        """Test Citation to_dict method."""
        citation = Citation(
            id=1,
            chat_message_id=1,
            document_id="doc-1",
            chunk_index=0,
            score=0.85,
            text_preview="Preview text..."
        )
        
        result = citation.to_dict()
        
        assert result["doc_id"] == "doc-1"
        assert result["chunk_index"] == 0
        assert result["score"] == 0.85
        assert result["text"] == "Preview text..."


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        yield f"sqlite:///{db_path}"
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create a test database manager."""
        return DatabaseManager(database_url=temp_db_path)
    
    def test_database_manager_initialization(self, temp_db_path):
        """Test DatabaseManager initializes correctly."""
        db = DatabaseManager(database_url=temp_db_path)
        
        assert db.engine is not None
        assert db.SessionLocal is not None
    
    def test_get_session(self, db_manager):
        """Test getting a database session."""
        session = db_manager.get_session()
        
        assert session is not None
        session.close()


class TestDocumentOperations:
    """Test document CRUD operations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        yield f"sqlite:///{db_path}"
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create a test database manager."""
        return DatabaseManager(database_url=temp_db_path)
    
    def test_create_document(self, db_manager):
        """Test creating a document."""
        doc = db_manager.create_document(
            doc_id="test-doc-1",
            filename="test.txt",
            content="Test content for the document.",
            content_type="text/plain"
        )
        
        assert doc.id == "test-doc-1"
        assert doc.filename == "test.txt"
        assert doc.size == len("Test content for the document.")
    
    def test_create_document_with_metadata(self, db_manager):
        """Test creating a document with metadata."""
        doc = db_manager.create_document(
            doc_id="meta-doc",
            filename="meta.txt",
            content="Content",
            metadata={"category": "HR", "version": "1.0"}
        )
        
        assert doc.id == "meta-doc"
    
    def test_get_document(self, db_manager):
        """Test retrieving a document."""
        # Create
        db_manager.create_document(
            doc_id="get-test",
            filename="get.txt",
            content="Get test content"
        )
        
        # Retrieve
        doc = db_manager.get_document("get-test")
        
        assert doc is not None
        assert doc.id == "get-test"
        assert doc.filename == "get.txt"
    
    def test_get_nonexistent_document(self, db_manager):
        """Test retrieving a nonexistent document."""
        doc = db_manager.get_document("nonexistent-id")
        
        assert doc is None
    
    def test_get_all_documents(self, db_manager):
        """Test getting all documents."""
        # Create multiple documents
        for i in range(3):
            db_manager.create_document(
                doc_id=f"all-doc-{i}",
                filename=f"doc{i}.txt",
                content=f"Content {i}"
            )
        
        docs = db_manager.get_all_documents()
        
        assert len(docs) == 3
    
    def test_update_document_indexed(self, db_manager):
        """Test marking a document as indexed."""
        db_manager.create_document(
            doc_id="index-test",
            filename="index.txt",
            content="Index content"
        )
        
        result = db_manager.update_document_indexed("index-test", chunk_count=5)
        
        assert result is True
        
        doc = db_manager.get_document("index-test")
        assert doc.is_indexed is True
        assert doc.chunk_count == 5
    
    def test_delete_document(self, db_manager):
        """Test deleting a document."""
        db_manager.create_document(
            doc_id="delete-test",
            filename="delete.txt",
            content="Delete content"
        )
        
        result = db_manager.delete_document("delete-test")
        
        assert result is True
        assert db_manager.get_document("delete-test") is None
    
    def test_delete_nonexistent_document(self, db_manager):
        """Test deleting a nonexistent document."""
        result = db_manager.delete_document("nonexistent")
        
        assert result is False


class TestChatOperations:
    """Test chat message operations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        yield f"sqlite:///{db_path}"
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create a test database manager."""
        return DatabaseManager(database_url=temp_db_path)
    
    def test_save_chat_message_user(self, db_manager):
        """Test saving a user message."""
        msg = db_manager.save_chat_message(
            user_id="user-1",
            role="user",
            content="What is the leave policy?"
        )
        
        assert msg.id is not None
        assert msg.user_id == "user-1"
        assert msg.role == "user"
        assert msg.content == "What is the leave policy?"
    
    def test_save_chat_message_assistant(self, db_manager):
        """Test saving an assistant message."""
        msg = db_manager.save_chat_message(
            user_id="user-1",
            role="assistant",
            content="The leave policy allows 20 days.",
            provider="ollama",
            model="llama3.1:8b"
        )
        
        assert msg.role == "assistant"
        assert msg.provider == "ollama"
        assert msg.model == "llama3.1:8b"
    
    def test_save_chat_message_with_citations(self, db_manager):
        """Test saving a message with citations."""
        # First create a document
        db_manager.create_document(
            doc_id="cited-doc",
            filename="cited.txt",
            content="Cited content"
        )
        
        msg = db_manager.save_chat_message(
            user_id="user-1",
            role="assistant",
            content="Response with citation",
            citations=[{
                "doc_id": "cited-doc",
                "chunk_index": 0,
                "score": 0.85,
                "text": "Cited text preview"
            }]
        )
        
        assert msg.id is not None
    
    def test_get_chat_history(self, db_manager):
        """Test retrieving chat history."""
        # Save multiple messages
        for i in range(5):
            db_manager.save_chat_message(
                user_id="history-user",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
        
        history = db_manager.get_chat_history("history-user")
        
        assert len(history) == 5
    
    def test_get_chat_history_limit(self, db_manager):
        """Test chat history respects limit."""
        for i in range(10):
            db_manager.save_chat_message(
                user_id="limit-user",
                role="user",
                content=f"Message {i}"
            )
        
        history = db_manager.get_chat_history("limit-user", limit=5)
        
        assert len(history) == 5
    
    def test_get_chat_history_isolated_by_user(self, db_manager):
        """Test chat history is isolated by user."""
        db_manager.save_chat_message(
            user_id="user-a",
            role="user",
            content="User A message"
        )
        db_manager.save_chat_message(
            user_id="user-b",
            role="user",
            content="User B message"
        )
        
        history_a = db_manager.get_chat_history("user-a")
        history_b = db_manager.get_chat_history("user-b")
        
        assert len(history_a) == 1
        assert len(history_b) == 1
        assert history_a[0].content == "User A message"
        assert history_b[0].content == "User B message"
    
    def test_clear_chat_history(self, db_manager):
        """Test clearing chat history."""
        for i in range(5):
            db_manager.save_chat_message(
                user_id="clear-user",
                role="user",
                content=f"Message {i}"
            )
        
        count = db_manager.clear_chat_history("clear-user")
        
        assert count == 5
        
        history = db_manager.get_chat_history("clear-user")
        assert len(history) == 0
    
    def test_clear_chat_history_only_affects_user(self, db_manager):
        """Test clearing only affects specific user."""
        db_manager.save_chat_message(
            user_id="keep-user",
            role="user",
            content="Keep this"
        )
        db_manager.save_chat_message(
            user_id="clear-this-user",
            role="user",
            content="Clear this"
        )
        
        db_manager.clear_chat_history("clear-this-user")
        
        keep_history = db_manager.get_chat_history("keep-user")
        assert len(keep_history) == 1


class TestDatabaseStats:
    """Test database statistics."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        yield f"sqlite:///{db_path}"
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def populated_db(self, temp_db_path):
        """Create and populate a test database."""
        db = DatabaseManager(database_url=temp_db_path)
        
        # Add documents
        for i in range(3):
            doc = db.create_document(
                doc_id=f"stats-doc-{i}",
                filename=f"stats{i}.txt",
                content=f"Stats content {i}"
            )
            if i < 2:
                db.update_document_indexed(f"stats-doc-{i}", chunk_count=5)
        
        # Add messages from different users
        for user in ["user-1", "user-2"]:
            for j in range(2):
                db.save_chat_message(
                    user_id=user,
                    role="user",
                    content=f"Message from {user}"
                )
        
        return db
    
    def test_get_stats(self, populated_db):
        """Test getting database statistics."""
        stats = populated_db.get_stats()
        
        assert "total_documents" in stats
        assert "indexed_documents" in stats
        assert "total_messages" in stats
        assert "unique_users" in stats
        
        assert stats["total_documents"] == 3
        assert stats["indexed_documents"] == 2
        assert stats["total_messages"] == 4
        assert stats["unique_users"] == 2


class TestDatabaseEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        yield f"sqlite:///{db_path}"
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_unicode_content(self, temp_db_path):
        """Test handling unicode content."""
        db = DatabaseManager(database_url=temp_db_path)
        
        doc = db.create_document(
            doc_id="unicode-doc",
            filename="unicode.txt",
            content="Unicode: 日本語 한국어 العربية 中文"
        )
        
        retrieved = db.get_document("unicode-doc")
        assert "日本語" in retrieved.content
    
    def test_very_long_content(self, temp_db_path):
        """Test handling very long content."""
        db = DatabaseManager(database_url=temp_db_path)
        
        long_content = "A" * 100000  # 100KB
        
        doc = db.create_document(
            doc_id="long-doc",
            filename="long.txt",
            content=long_content
        )
        
        assert doc.size == 100000
    
    def test_special_characters_in_content(self, temp_db_path):
        """Test handling special characters."""
        db = DatabaseManager(database_url=temp_db_path)
        
        db.save_chat_message(
            user_id="special-user",
            role="user",
            content="Special: @#$%^&*() <script>alert('xss')</script>"
        )
        
        history = db.get_chat_history("special-user")
        assert len(history) == 1
        assert "<script>" in history[0].content
    
    def test_empty_content(self, temp_db_path):
        """Test handling empty content."""
        db = DatabaseManager(database_url=temp_db_path)
        
        doc = db.create_document(
            doc_id="empty-doc",
            filename="empty.txt",
            content=""
        )
        
        assert doc.size == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
