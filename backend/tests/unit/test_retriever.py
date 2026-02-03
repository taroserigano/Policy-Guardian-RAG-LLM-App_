"""
Comprehensive Test Suite for RAG Retriever Module
Tests document indexing, retrieval, and context building
"""
import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.retriever import RAGRetriever, RetrievalResult, get_retriever
from app.rag.vector_store import VectorStore


class TestRetrievalResultDataclass:
    """Test the RetrievalResult dataclass."""
    
    def test_create_retrieval_result(self):
        """Test creating a RetrievalResult."""
        result = RetrievalResult(
            text="Sample text",
            doc_id="doc-1",
            filename="test.txt",
            chunk_index=0,
            score=0.85,
            section="Introduction"
        )
        
        assert result.text == "Sample text"
        assert result.doc_id == "doc-1"
        assert result.filename == "test.txt"
        assert result.chunk_index == 0
        assert result.score == 0.85
        assert result.section == "Introduction"
    
    def test_retrieval_result_optional_section(self):
        """Test RetrievalResult with no section."""
        result = RetrievalResult(
            text="Text",
            doc_id="doc-1",
            filename="file.txt",
            chunk_index=0,
            score=0.5
        )
        
        assert result.section is None


class TestRAGRetriever:
    """Test cases for RAGRetriever class."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def retriever(self, temp_persist_dir):
        """Create a test retriever instance."""
        return RAGRetriever(persist_directory=temp_persist_dir)
    
    def test_retriever_initialization(self, temp_persist_dir):
        """Test RAGRetriever initializes correctly."""
        retriever = RAGRetriever(persist_directory=temp_persist_dir)
        
        assert retriever.vector_store is not None
    
    def test_index_document_basic(self, retriever):
        """Test basic document indexing."""
        content = """
        LEAVE POLICY
        
        1. Annual Leave
        Employees are entitled to 20 days of paid leave per year.
        
        2. Sick Leave
        10 days of paid sick leave are provided.
        """
        
        num_chunks = retriever.index_document(
            doc_id="leave-policy",
            content=content,
            filename="leave_policy.txt"
        )
        
        assert num_chunks > 0
    
    def test_index_document_empty_content(self, retriever):
        """Test indexing empty content."""
        num_chunks = retriever.index_document(
            doc_id="empty-doc",
            content="",
            filename="empty.txt"
        )
        
        assert num_chunks == 0
    
    def test_index_document_with_custom_chunk_size(self, retriever):
        """Test indexing with custom chunk sizes."""
        content = "This is content. " * 100
        
        num_chunks = retriever.index_document(
            doc_id="custom-doc",
            content=content,
            filename="custom.txt",
            chunk_size=100,
            chunk_overlap=10
        )
        
        assert num_chunks > 1
    
    def test_retrieve_basic(self, retriever):
        """Test basic retrieval."""
        # Index a document first
        content = """
        Data Privacy Policy
        
        All personal data must be encrypted.
        Access control is required for sensitive systems.
        """
        
        retriever.index_document(
            doc_id="privacy-policy",
            content=content,
            filename="privacy.txt"
        )
        
        # Retrieve
        results = retriever.retrieve(
            query="data encryption",
            n_results=3
        )
        
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], RetrievalResult)
    
    def test_retrieve_with_filter(self, retriever):
        """Test retrieval with document filter."""
        # Index multiple documents
        retriever.index_document(
            doc_id="doc-a",
            content="Content about vacations and time off.",
            filename="a.txt"
        )
        retriever.index_document(
            doc_id="doc-b",
            content="Content about vacations and holidays.",
            filename="b.txt"
        )
        
        # Filter to only doc-a
        results = retriever.retrieve(
            query="vacations",
            n_results=5,
            filter_doc_ids=["doc-a"]
        )
        
        for result in results:
            assert result.doc_id == "doc-a"
    
    def test_retrieve_min_score(self, retriever):
        """Test retrieval with minimum score."""
        retriever.index_document(
            doc_id="score-test",
            content="Specific technical content about quantum physics.",
            filename="physics.txt"
        )
        
        # Search with high min_score
        results = retriever.retrieve(
            query="quantum",
            n_results=5,
            min_score=0.3
        )
        
        # All results should meet minimum score
        for result in results:
            assert result.score >= 0.3


class TestContextBuilding:
    """Test context building functionality."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def retriever(self, temp_persist_dir):
        """Create populated retriever."""
        retriever = RAGRetriever(persist_directory=temp_persist_dir)
        
        # Add test documents
        retriever.index_document(
            doc_id="hr-policy",
            content="Annual leave is 20 days. Sick leave is 10 days. Remote work requires approval.",
            filename="hr_policy.txt"
        )
        
        return retriever
    
    def test_build_context_basic(self, retriever):
        """Test basic context building."""
        result = retriever.build_context(
            query="leave policy",
            n_results=3
        )
        
        assert "context" in result
        assert "citations" in result
        assert "num_chunks" in result
    
    def test_build_context_returns_citations(self, retriever):
        """Test context building includes citations."""
        result = retriever.build_context(
            query="annual leave days",
            n_results=3
        )
        
        if result["num_chunks"] > 0:
            assert len(result["citations"]) > 0
            citation = result["citations"][0]
            assert "doc_id" in citation
            assert "filename" in citation
            assert "score" in citation
    
    def test_build_context_max_length(self, retriever):
        """Test context respects max length."""
        result = retriever.build_context(
            query="leave",
            n_results=10,
            max_context_length=100
        )
        
        # Context should be within limit (approximately)
        assert len(result["context"]) <= 200  # Some buffer for formatting
    
    def test_build_context_empty_query(self, retriever):
        """Test context building with no matching results."""
        result = retriever.build_context(
            query="xyznonexistentquery123",
            n_results=3
        )
        
        # Should return empty context
        assert isinstance(result, dict)


class TestRetrieverDocumentManagement:
    """Test document management operations."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def retriever(self, temp_persist_dir):
        """Create retriever instance."""
        return RAGRetriever(persist_directory=temp_persist_dir)
    
    def test_delete_document(self, retriever):
        """Test document deletion."""
        # Index
        retriever.index_document(
            doc_id="delete-me",
            content="Content to delete",
            filename="delete.txt"
        )
        
        assert "delete-me" in retriever.get_indexed_documents()
        
        # Delete
        deleted = retriever.delete_document("delete-me")
        assert deleted > 0
        
        assert "delete-me" not in retriever.get_indexed_documents()
    
    def test_get_indexed_documents(self, retriever):
        """Test getting list of indexed documents."""
        retriever.index_document(
            doc_id="doc-1",
            content="Content 1",
            filename="1.txt"
        )
        retriever.index_document(
            doc_id="doc-2",
            content="Content 2",
            filename="2.txt"
        )
        
        docs = retriever.get_indexed_documents()
        
        assert "doc-1" in docs
        assert "doc-2" in docs
    
    def test_get_stats(self, retriever):
        """Test retriever statistics."""
        retriever.index_document(
            doc_id="stats-doc",
            content="Content for stats test with multiple sentences.",
            filename="stats.txt"
        )
        
        stats = retriever.get_stats()
        
        assert "total_chunks" in stats
        assert "unique_documents" in stats
        assert stats["total_chunks"] >= 1
        assert stats["unique_documents"] >= 1


class TestGetRetrieverFunction:
    """Test the get_retriever singleton function."""
    
    def test_get_retriever_creates_instance(self):
        """Test that get_retriever creates an instance."""
        # Note: This test may be affected by global state
        # In a real scenario, you'd want to reset the singleton
        temp_dir = tempfile.mkdtemp()
        try:
            retriever = get_retriever(persist_directory=temp_dir)
            assert retriever is not None
            assert isinstance(retriever, RAGRetriever)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestRetrieverEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_unicode_content(self, temp_persist_dir):
        """Test indexing and retrieving unicode content."""
        retriever = RAGRetriever(persist_directory=temp_persist_dir)
        
        retriever.index_document(
            doc_id="unicode-doc",
            content="Unicode content: 日本語 한국어 العربية",
            filename="unicode.txt"
        )
        
        results = retriever.retrieve("日本語", n_results=3)
        assert isinstance(results, list)
    
    def test_special_characters(self, temp_persist_dir):
        """Test content with special characters."""
        retriever = RAGRetriever(persist_directory=temp_persist_dir)
        
        retriever.index_document(
            doc_id="special-doc",
            content="Special: @#$%^&*() <script>alert('test')</script>",
            filename="special.txt"
        )
        
        # Should not crash
        stats = retriever.get_stats()
        assert stats["total_chunks"] >= 1
    
    def test_very_long_content(self, temp_persist_dir):
        """Test very long content."""
        retriever = RAGRetriever(persist_directory=temp_persist_dir)
        
        long_content = "This is a sentence. " * 1000
        
        num_chunks = retriever.index_document(
            doc_id="long-doc",
            content=long_content,
            filename="long.txt"
        )
        
        # Should create multiple chunks
        assert num_chunks > 1
    
    def test_multiple_documents_same_query(self, temp_persist_dir):
        """Test retrieval across multiple documents."""
        retriever = RAGRetriever(persist_directory=temp_persist_dir)
        
        for i in range(5):
            retriever.index_document(
                doc_id=f"multi-doc-{i}",
                content=f"Document {i} about company policies and procedures.",
                filename=f"doc{i}.txt"
            )
        
        results = retriever.retrieve("company policies", n_results=10)
        
        # Should find results from multiple documents
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
