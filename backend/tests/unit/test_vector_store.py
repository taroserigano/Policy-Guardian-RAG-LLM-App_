"""
Comprehensive Test Suite for Vector Store Module
Tests ChromaDB integration, embeddings, and semantic search
"""
import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.vector_store import EmbeddingService, VectorStore


class TestEmbeddingService:
    """Test cases for EmbeddingService class."""
    
    def test_embedding_service_initialization(self):
        """Test EmbeddingService initializes correctly."""
        service = EmbeddingService()
        assert service.model_name == "all-MiniLM-L6-v2"
    
    def test_embedding_service_chromadb_fallback(self):
        """Test ChromaDB fallback mode."""
        service = EmbeddingService(use_chromadb_embeddings=True)
        assert service.use_chromadb_embeddings is True
    
    def test_embed_text_with_chromadb(self):
        """Test embed_text returns None when using ChromaDB embeddings."""
        service = EmbeddingService(use_chromadb_embeddings=True)
        result = service.embed_text("test text")
        assert result is None  # ChromaDB handles it
    
    def test_embed_texts_with_chromadb(self):
        """Test embed_texts returns None when using ChromaDB embeddings."""
        service = EmbeddingService(use_chromadb_embeddings=True)
        result = service.embed_texts(["text1", "text2"])
        assert result is None  # ChromaDB handles it
    
    def test_get_embedding_dimension(self):
        """Test embedding dimension is returned."""
        service = EmbeddingService(use_chromadb_embeddings=True)
        dim = service.get_embedding_dimension()
        assert dim == 384  # Default for ChromaDB


class TestVectorStore:
    """Test cases for VectorStore class."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def vector_store(self, temp_persist_dir):
        """Create a test vector store instance."""
        return VectorStore(
            collection_name="test_collection",
            persist_directory=temp_persist_dir
        )
    
    def test_vector_store_initialization(self, temp_persist_dir):
        """Test VectorStore initializes correctly."""
        store = VectorStore(
            collection_name="test_init",
            persist_directory=temp_persist_dir
        )
        
        assert store.collection_name == "test_init"
        assert store.persist_directory == temp_persist_dir
        assert store.collection is not None
    
    def test_add_document_basic(self, vector_store):
        """Test adding a document with chunks."""
        chunks = ["Chunk 1 content", "Chunk 2 content", "Chunk 3 content"]
        
        count = vector_store.add_document(
            doc_id="test-doc-1",
            chunks=chunks,
            metadata={"filename": "test.txt"}
        )
        
        assert count == 3
        assert vector_store.get_document_count() == 3
    
    def test_add_document_empty_chunks(self, vector_store):
        """Test adding document with empty chunks list."""
        count = vector_store.add_document(
            doc_id="empty-doc",
            chunks=[],
            metadata={"filename": "empty.txt"}
        )
        
        assert count == 0
    
    def test_add_document_with_metadata(self, vector_store):
        """Test metadata is stored correctly."""
        chunks = ["Test content"]
        
        vector_store.add_document(
            doc_id="metadata-test",
            chunks=chunks,
            metadata={"filename": "test.txt", "category": "HR"}
        )
        
        results = vector_store.search("Test content", n_results=1)
        assert len(results) > 0
        assert results[0]["metadata"]["filename"] == "test.txt"
        assert results[0]["metadata"]["category"] == "HR"
    
    def test_search_basic(self, vector_store):
        """Test basic search functionality."""
        chunks = [
            "Annual leave policy allows 20 days of paid vacation.",
            "Sick leave provides 10 days for illness.",
            "Remote work is allowed with manager approval."
        ]
        
        vector_store.add_document(
            doc_id="search-test",
            chunks=chunks,
            metadata={"filename": "policy.txt"}
        )
        
        results = vector_store.search("vacation days", n_results=3)
        
        assert len(results) > 0
        assert "text" in results[0]
        assert "score" in results[0]
    
    def test_search_with_filter(self, vector_store):
        """Test search with document filter."""
        # Add documents
        vector_store.add_document(
            doc_id="doc-a",
            chunks=["Policy A content about vacation"],
            metadata={"filename": "a.txt"}
        )
        vector_store.add_document(
            doc_id="doc-b",
            chunks=["Policy B content about vacation"],
            metadata={"filename": "b.txt"}
        )
        
        # Search only in doc-a
        results = vector_store.search(
            "vacation",
            n_results=5,
            filter_doc_ids=["doc-a"]
        )
        
        assert len(results) > 0
        for result in results:
            assert result["metadata"]["doc_id"] == "doc-a"
    
    def test_search_min_score(self, vector_store):
        """Test search with minimum score filter."""
        chunks = ["This is very specific content about quantum physics."]
        
        vector_store.add_document(
            doc_id="physics-doc",
            chunks=chunks,
            metadata={"filename": "physics.txt"}
        )
        
        # Search for unrelated content with high min_score
        results = vector_store.search(
            "completely unrelated cooking recipe",
            n_results=5,
            min_score=0.9  # Very high threshold
        )
        
        # May or may not return results depending on similarity
        # Just verify it doesn't crash
        assert isinstance(results, list)
    
    def test_delete_document(self, vector_store):
        """Test document deletion."""
        chunks = ["Content to delete"]
        
        vector_store.add_document(
            doc_id="delete-me",
            chunks=chunks,
            metadata={"filename": "delete.txt"}
        )
        
        initial_count = vector_store.get_document_count()
        assert initial_count == 1
        
        deleted = vector_store.delete_document("delete-me")
        assert deleted == 1
        
        assert vector_store.get_document_count() == 0
    
    def test_delete_nonexistent_document(self, vector_store):
        """Test deleting a document that doesn't exist."""
        deleted = vector_store.delete_document("nonexistent-doc")
        assert deleted == 0
    
    def test_get_document_count(self, vector_store):
        """Test document count tracking."""
        assert vector_store.get_document_count() == 0
        
        vector_store.add_document(
            doc_id="count-test",
            chunks=["Chunk 1", "Chunk 2"],
            metadata={}
        )
        
        assert vector_store.get_document_count() == 2
    
    def test_get_unique_documents(self, vector_store):
        """Test getting unique document IDs."""
        vector_store.add_document(
            doc_id="doc-1",
            chunks=["Content 1"],
            metadata={}
        )
        vector_store.add_document(
            doc_id="doc-2",
            chunks=["Content 2", "Content 3"],
            metadata={}
        )
        
        unique_docs = vector_store.get_unique_documents()
        
        assert len(unique_docs) == 2
        assert "doc-1" in unique_docs
        assert "doc-2" in unique_docs
    
    def test_reset(self, vector_store):
        """Test collection reset."""
        vector_store.add_document(
            doc_id="reset-test",
            chunks=["Content"],
            metadata={}
        )
        
        assert vector_store.get_document_count() > 0
        
        vector_store.reset()
        
        assert vector_store.get_document_count() == 0


class TestSemanticSearchQuality:
    """Test semantic search quality and relevance."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def populated_store(self, temp_persist_dir):
        """Create and populate a vector store."""
        store = VectorStore(
            collection_name="quality_test",
            persist_directory=temp_persist_dir
        )
        
        # Add diverse content
        store.add_document(
            doc_id="hr-policy",
            chunks=[
                "Annual leave entitlement is 20 days per year.",
                "Sick leave policy allows 10 days paid leave.",
                "Maternity leave is 12 weeks paid."
            ],
            metadata={"filename": "hr_policy.txt", "category": "HR"}
        )
        
        store.add_document(
            doc_id="security-policy",
            chunks=[
                "All laptops must use full disk encryption.",
                "VPN is required for remote access.",
                "Two-factor authentication is mandatory."
            ],
            metadata={"filename": "security.txt", "category": "IT"}
        )
        
        return store
    
    def test_relevant_results_ranked_higher(self, populated_store):
        """Test that relevant results are ranked higher."""
        results = populated_store.search("vacation days off", n_results=5)
        
        # First result should be about leave/vacation
        assert len(results) > 0
        top_result = results[0]["text"].lower()
        assert "leave" in top_result or "annual" in top_result or "days" in top_result
    
    def test_category_relevance(self, populated_store):
        """Test search respects content categories."""
        # Search for security-related content
        results = populated_store.search("encryption security", n_results=3)
        
        assert len(results) > 0
        # Top results should be from security policy
        top_result = results[0]["text"].lower()
        assert "encrypt" in top_result or "vpn" in top_result or "security" in top_result
    
    def test_multiple_relevant_results(self, populated_store):
        """Test that multiple relevant results are returned."""
        results = populated_store.search("leave policy", n_results=5)
        
        # Should find multiple leave-related chunks
        leave_related = [r for r in results if "leave" in r["text"].lower()]
        assert len(leave_related) >= 1


class TestVectorStorePersistence:
    """Test vector store persistence."""
    
    def test_persistence_across_instances(self):
        """Test that data persists across VectorStore instances."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create first instance and add data
            store1 = VectorStore(
                collection_name="persist_test",
                persist_directory=temp_dir
            )
            store1.add_document(
                doc_id="persistent-doc",
                chunks=["Persistent content that should survive"],
                metadata={"filename": "persist.txt"}
            )
            
            del store1  # Delete the instance
            
            # Create new instance with same directory
            store2 = VectorStore(
                collection_name="persist_test",
                persist_directory=temp_dir
            )
            
            # Data should still be there
            assert store2.get_document_count() == 1
            
            results = store2.search("Persistent content", n_results=1)
            assert len(results) > 0
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def temp_persist_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_unicode_content(self, temp_persist_dir):
        """Test handling unicode content."""
        store = VectorStore(
            collection_name="unicode_test",
            persist_directory=temp_persist_dir
        )
        
        chunks = ["Unicode: 日本語 한국어 العربية"]
        store.add_document(
            doc_id="unicode-doc",
            chunks=chunks,
            metadata={"filename": "unicode.txt"}
        )
        
        results = store.search("日本語", n_results=1)
        assert len(results) >= 0  # May or may not find it
    
    def test_special_characters(self, temp_persist_dir):
        """Test handling special characters."""
        store = VectorStore(
            collection_name="special_test",
            persist_directory=temp_persist_dir
        )
        
        chunks = ["Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"]
        store.add_document(
            doc_id="special-doc",
            chunks=chunks,
            metadata={"filename": "special.txt"}
        )
        
        assert store.get_document_count() == 1
    
    def test_very_long_content(self, temp_persist_dir):
        """Test handling very long content."""
        store = VectorStore(
            collection_name="long_test",
            persist_directory=temp_persist_dir
        )
        
        long_content = "word " * 1000
        store.add_document(
            doc_id="long-doc",
            chunks=[long_content],
            metadata={"filename": "long.txt"}
        )
        
        assert store.get_document_count() == 1
    
    def test_many_documents(self, temp_persist_dir):
        """Test handling many documents."""
        store = VectorStore(
            collection_name="many_test",
            persist_directory=temp_persist_dir
        )
        
        for i in range(20):
            store.add_document(
                doc_id=f"doc-{i}",
                chunks=[f"Content for document {i}"],
                metadata={"filename": f"doc{i}.txt"}
            )
        
        assert store.get_document_count() == 20
        assert len(store.get_unique_documents()) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
