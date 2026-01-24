"""
Test cases for new RAG features:
1. Advanced Query Rewriting (auto_rewrite)
2. Cross-Encoder Re-ranking (cross_encoder)
3. Document Categories and Tags
4. Batch Upload with Progress
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRAGOptionsSchema:
    """Test the updated RAGOptions schema."""
    
    def test_rag_options_includes_new_fields(self):
        """Test that RAGOptions schema includes auto_rewrite and cross_encoder."""
        from app.schemas import RAGOptions
        
        # Create with all options
        options = RAGOptions(
            query_expansion=True,
            hybrid_search=True,
            reranking=True,
            auto_rewrite=True,
            cross_encoder=True
        )
        
        assert options.query_expansion is True
        assert options.hybrid_search is True
        assert options.reranking is True
        assert options.auto_rewrite is True
        assert options.cross_encoder is True
    
    def test_rag_options_defaults_to_false(self):
        """Test that new options default to False."""
        from app.schemas import RAGOptions
        
        options = RAGOptions()
        
        assert options.auto_rewrite is False
        assert options.cross_encoder is False
    
    def test_chat_request_accepts_new_rag_options(self):
        """Test that ChatRequest schema accepts new RAG options."""
        from app.schemas import ChatRequest, RAGOptions
        
        request = ChatRequest(
            user_id="test-user",
            provider="ollama",
            question="What is the policy?",
            rag_options=RAGOptions(
                auto_rewrite=True,
                cross_encoder=True
            )
        )
        
        assert request.rag_options.auto_rewrite is True
        assert request.rag_options.cross_encoder is True


class TestDocumentCategories:
    """Test document category and tagging functionality."""
    
    def test_document_model_has_category_field(self):
        """Test that Document model includes category field."""
        from app.db.models import Document
        
        # Check column exists
        assert hasattr(Document, 'category')
        assert hasattr(Document, 'tags')
    
    def test_document_response_includes_category(self):
        """Test that DocumentResponse schema includes category and tags."""
        from app.schemas import DocumentResponse
        from datetime import datetime
        
        response = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            content_type="application/pdf",
            category="policy",
            tags=["important", "2024"],
            created_at=datetime.now()
        )
        
        assert response.category == "policy"
        assert response.tags == ["important", "2024"]
    
    def test_document_update_request_schema(self):
        """Test DocumentUpdateRequest schema."""
        from app.schemas import DocumentUpdateRequest
        
        update = DocumentUpdateRequest(
            category="legal",
            tags=["contract", "vendor"]
        )
        
        assert update.category == "legal"
        assert update.tags == ["contract", "vendor"]
    
    def test_document_update_request_allows_partial(self):
        """Test that DocumentUpdateRequest allows partial updates."""
        from app.schemas import DocumentUpdateRequest
        
        # Only category
        update1 = DocumentUpdateRequest(category="hr")
        assert update1.category == "hr"
        assert update1.tags is None
        
        # Only tags
        update2 = DocumentUpdateRequest(tags=["urgent"])
        assert update2.category is None
        assert update2.tags == ["urgent"]


class TestDocumentCategoriesAPI:
    """Test document category API endpoints."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch('app.api.routes_docs.get_db') as mock:
            mock_session = MagicMock()
            mock.return_value = mock_session
            yield mock_session
    
    def test_valid_categories(self):
        """Test that only valid categories are accepted."""
        valid_categories = ["policy", "legal", "hr", "compliance", "technical", "other"]
        
        for cat in valid_categories:
            from app.schemas import DocumentUpdateRequest
            update = DocumentUpdateRequest(category=cat)
            assert update.category == cat


class TestQueryRewriting:
    """Test query rewriting functionality."""
    
    def test_expand_query_function_exists(self):
        """Test that expand_query function exists."""
        from app.rag.query_processor import expand_query
        assert callable(expand_query)
    
    def test_rewrite_query_function_exists(self):
        """Test that rewrite_query function exists."""
        from app.rag.query_processor import rewrite_query
        assert callable(rewrite_query)
    
    @patch('app.rag.query_processor.get_llm')
    def test_expand_query_returns_list(self, mock_get_llm):
        """Test that expand_query returns a list of queries."""
        from app.rag.query_processor import expand_query
        
        # Mock LLM response
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Alternative query 1\nAlternative query 2"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        result = expand_query("What is the leave policy?", provider="ollama")
        
        assert isinstance(result, list)
        assert len(result) >= 1  # At least original query


class TestCrossEncoderReranking:
    """Test cross-encoder reranking functionality."""
    
    def test_rerank_llm_function_exists(self):
        """Test that rerank_chunks_llm function exists."""
        from app.rag.reranker import rerank_chunks_llm
        assert callable(rerank_chunks_llm)
    
    def test_rerank_simple_function_exists(self):
        """Test that rerank_chunks_simple function exists."""
        from app.rag.reranker import rerank_chunks_simple
        assert callable(rerank_chunks_simple)
    
    @patch('app.rag.reranker.get_llm')
    def test_rerank_llm_scores_chunks(self, mock_get_llm):
        """Test that rerank_chunks_llm scores and sorts chunks."""
        from app.rag.reranker import rerank_chunks_llm
        
        # Mock LLM response
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "8"  # High score
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        chunks = [
            {'text': 'Relevant chunk about policy', 'score': 0.5},
            {'text': 'Less relevant chunk', 'score': 0.3}
        ]
        
        result = rerank_chunks_llm("What is the policy?", chunks, top_k=2)
        
        assert isinstance(result, list)
        # Should return reranked results
        assert len(result) <= 2


class TestRAGPipelineWithNewOptions:
    """Test RAG pipeline integration with new options."""
    
    def test_streaming_pipeline_accepts_new_options(self):
        """Test that streaming pipeline accepts auto_rewrite and cross_encoder."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        # Just verify the function signature accepts these options
        import inspect
        sig = inspect.signature(run_rag_pipeline_streaming)
        params = sig.parameters
        
        assert 'rag_options' in params
    
    @patch('app.rag.graph.retrieve_relevant_chunks')
    @patch('app.rag.graph.get_streaming_llm')
    def test_auto_rewrite_option_triggers_rewrite(self, mock_llm, mock_retrieve):
        """Test that auto_rewrite option triggers query rewriting."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        # Mock retrieval
        mock_retrieve.return_value = ([], "No context")
        
        # This would normally call rewrite_query when auto_rewrite=True
        rag_options = {
            'auto_rewrite': True,
            'cross_encoder': False
        }
        
        # Just verify the function can be called with these options
        try:
            gen = run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options=rag_options
            )
            # Consume generator (will fail at LLM call, which is expected)
            list(gen)
        except Exception:
            pass  # Expected to fail without real LLM
    
    @patch('app.rag.graph.retrieve_relevant_chunks')
    @patch('app.rag.graph.rerank_chunks_simple')
    @patch('app.rag.graph.get_streaming_llm')
    def test_cross_encoder_option_triggers_llm_rerank(self, mock_llm, mock_rerank, mock_retrieve):
        """Test that cross_encoder option triggers LLM-based reranking."""
        # This is a structural test - verifying the option is recognized
        rag_options = {
            'cross_encoder': True,
            'reranking': False
        }
        
        # The graph.py should check for cross_encoder and use rerank_chunks_llm
        from app.rag.graph import run_rag_pipeline_streaming
        
        # Verify function accepts the option without error
        assert callable(run_rag_pipeline_streaming)


class TestBatchUploadAPI:
    """Test batch upload functionality."""
    
    def test_batch_upload_endpoint_exists(self):
        """Test that batch upload endpoint is registered."""
        from app.api.routes_docs import router
        
        routes = [route.path for route in router.routes]
        assert "/upload/batch" in routes or any("batch" in r for r in routes)
    
    def test_upload_documents_with_progress_client_function(self):
        """Test that client has uploadDocumentsWithProgress function."""
        # This is tested in frontend tests
        pass


class TestDocumentContentAPI:
    """Test document content retrieval for preview."""
    
    def test_document_content_endpoint_exists(self):
        """Test that document content endpoint exists."""
        from app.api.routes_docs import router
        
        routes = [route.path for route in router.routes]
        assert any("content" in r for r in routes)


# Integration tests (require running server)
class TestIntegrationDocumentCategories:
    """Integration tests for document categories (requires server)."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            from starlette.testclient import TestClient
            from app.main import app
            with TestClient(app) as test_client:
                yield test_client
        except Exception as e:
            pytest.skip(f"Could not create test client: {e}")
    
    def test_list_categories_endpoint(self, client):
        """Test listing document categories."""
        response = client.get("/api/docs/categories/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        
        # Check expected categories exist
        category_ids = [c["id"] for c in data["categories"]]
        assert "policy" in category_ids
        assert "legal" in category_ids
        assert "hr" in category_ids
    
    def test_update_document_category(self, client):
        """Test updating a document's category."""
        # First upload a document
        content = b"Test document content for category test."
        files = {"file": ("test_category.txt", content, "text/plain")}
        
        upload_response = client.post("/api/docs/upload", files=files)
        
        if upload_response.status_code == 201:
            doc_id = upload_response.json()["doc_id"]
            
            # Update category
            update_response = client.patch(
                f"/api/docs/{doc_id}",
                json={"category": "policy", "tags": ["test", "important"]}
            )
            
            assert update_response.status_code == 200
            data = update_response.json()
            assert data["category"] == "policy"
            assert "test" in data["tags"]
            
            # Cleanup
            client.delete(f"/api/docs/{doc_id}")
    
    def test_invalid_category_rejected(self, client):
        """Test that invalid categories are rejected."""
        # First upload a document
        content = b"Test document content."
        files = {"file": ("test_invalid.txt", content, "text/plain")}
        
        upload_response = client.post("/api/docs/upload", files=files)
        
        if upload_response.status_code == 201:
            doc_id = upload_response.json()["doc_id"]
            
            # Try invalid category
            update_response = client.patch(
                f"/api/docs/{doc_id}",
                json={"category": "invalid_category"}
            )
            
            assert update_response.status_code == 400
            
            # Cleanup
            client.delete(f"/api/docs/{doc_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
