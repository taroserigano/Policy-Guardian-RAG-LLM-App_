"""
Comprehensive Test Suite for Production Server API
Tests all API endpoints with HTTPX AsyncClient
"""
import pytest
import pytest_asyncio
import sys
import tempfile
import shutil
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


@pytest.fixture(scope="module")
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def test_app(temp_data_dir):
    """Create test app with isolated data directory."""
    os.environ["DATA_DIR"] = temp_data_dir
    from production_server import app
    return app


@pytest_asyncio.fixture
async def client(test_app):
    """Create async test client."""
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test basic health check."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "version" in data
        assert "features" in data
    
    @pytest.mark.asyncio
    async def test_health_features_present(self, client):
        """Test health check returns feature flags."""
        response = await client.get("/health")
        data = response.json()
        
        assert "rag_enabled" in data["features"]
        assert "vector_store" in data["features"]
        assert "database" in data["features"]


class TestRootEndpoint:
    """Test root endpoint."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root returns API info."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_root_lists_endpoints(self, client):
        """Test root lists available endpoints."""
        response = await client.get("/")
        data = response.json()
        
        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "docs" in endpoints
        assert "chat" in endpoints


class TestDocumentEndpoints:
    """Test document management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client):
        """Test listing documents when empty."""
        response = await client.get("/api/docs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    @pytest.mark.asyncio
    async def test_upload_document(self, client):
        """Test uploading a document."""
        content = b"This is test content for the policy document."
        files = {"file": ("test_policy.txt", content, "text/plain")}
        
        response = await client.post("/api/docs/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "id" in data
        assert data["filename"] == "test_policy.txt"
    
    @pytest.mark.asyncio
    async def test_upload_and_list_document(self, client):
        """Test that uploaded document appears in list."""
        content = b"Another test document content."
        files = {"file": ("another_doc.txt", content, "text/plain")}
        
        upload_response = await client.post("/api/docs/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        list_response = await client.get("/api/docs")
        docs = list_response.json()["documents"]
        
        assert any(d["id"] == doc_id for d in docs)
    
    @pytest.mark.asyncio
    async def test_delete_document(self, client):
        """Test deleting a document."""
        # Upload first
        content = b"Document to delete."
        files = {"file": ("delete_me.txt", content, "text/plain")}
        upload_response = await client.post("/api/docs/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        # Delete
        delete_response = await client.delete(f"/api/docs/{doc_id}")
        
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True


class TestChatEndpoint:
    """Test chat endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_basic(self, client):
        """Test basic chat request."""
        response = await client.post("/api/chat", json={
            "question": "What is the company policy?",
            "provider": "ollama"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "citations" in data
        assert "model" in data
    
    @pytest.mark.asyncio
    async def test_chat_with_user_id(self, client):
        """Test chat with specific user ID."""
        response = await client.post("/api/chat", json={
            "question": "Hello",
            "provider": "ollama",
            "user_id": "test-user-123"
        })
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_chat_with_document_filter(self, client):
        """Test chat with document filter."""
        # Upload a document
        content = b"Remote work policy allows 2 days per week."
        files = {"file": ("remote_work.txt", content, "text/plain")}
        upload_response = await client.post("/api/docs/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        # Chat with filter
        response = await client.post("/api/chat", json={
            "question": "What about remote work?",
            "provider": "ollama",
            "doc_ids": [doc_id]
        })
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_chat_response_has_context_flag(self, client):
        """Test chat response has context_used flag."""
        response = await client.post("/api/chat", json={
            "question": "Tell me about policies",
            "provider": "ollama"
        })
        
        data = response.json()
        assert "context_used" in data
        assert isinstance(data["context_used"], bool)


class TestChatHistoryEndpoints:
    """Test chat history endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, client):
        """Test getting chat history."""
        # Send a message first
        await client.post("/api/chat", json={
            "question": "First question",
            "provider": "ollama",
            "user_id": "history-user-1"
        })
        
        # Get history
        response = await client.get("/api/chat/history?user_id=history-user-1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "messages" in data
    
    @pytest.mark.asyncio
    async def test_clear_chat_history(self, client):
        """Test clearing chat history."""
        # Send messages
        for i in range(3):
            await client.post("/api/chat", json={
                "question": f"Question {i}",
                "provider": "ollama",
                "user_id": "clear-history-user"
            })
        
        # Clear
        response = await client.post("/api/chat/clear?user_id=clear-history-user")
        
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestStatsEndpoint:
    """Test stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, client):
        """Test getting system stats."""
        response = await client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "rag_available" in data
        assert "vector_store" in data
        assert "database" in data
    
    @pytest.mark.asyncio
    async def test_stats_vector_store_info(self, client):
        """Test stats includes vector store info."""
        response = await client.get("/api/stats")
        data = response.json()
        
        if data["rag_available"]:
            vs_stats = data["vector_store"]
            assert "total_chunks" in vs_stats
            assert "unique_documents" in vs_stats
    
    @pytest.mark.asyncio
    async def test_stats_database_info(self, client):
        """Test stats includes database info."""
        response = await client.get("/api/stats")
        data = response.json()
        
        db_stats = data["database"]
        assert "total_documents" in db_stats
        assert "total_messages" in db_stats


class TestAPIValidation:
    """Test API validation."""
    
    @pytest.mark.asyncio
    async def test_chat_requires_question(self, client):
        """Test chat requires a question."""
        response = await client.post("/api/chat", json={
            "provider": "ollama"
        })
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_chat_multiple_providers(self, client):
        """Test chat works with different providers."""
        for provider in ["ollama", "openai", "anthropic"]:
            response = await client.post("/api/chat", json={
                "question": "Test",
                "provider": provider
            })
            assert response.status_code == 200


class TestDocumentation:
    """Test OpenAPI documentation."""
    
    @pytest.mark.asyncio
    async def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openapi" in data
        assert "paths" in data
    
    @pytest.mark.asyncio
    async def test_swagger_ui(self, client):
        """Test Swagger UI is available."""
        response = await client.get("/docs")
        
        assert response.status_code == 200


class TestEdgeCases:
    """Test edge cases."""
    
    @pytest.mark.asyncio
    async def test_upload_empty_content(self, client):
        """Test uploading empty content."""
        content = b""
        files = {"file": ("empty.txt", content, "text/plain")}
        
        response = await client.post("/api/docs/upload", files=files)
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_long_question(self, client):
        """Test handling long question."""
        long_question = "What is " + "the policy " * 50 + "about?"
        
        response = await client.post("/api/chat", json={
            "question": long_question,
            "provider": "ollama"
        })
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_unicode_in_document(self, client):
        """Test unicode in document."""
        content = "Unicode: 日本語 한국어".encode('utf-8')
        files = {"file": ("unicode.txt", content, "text/plain")}
        
        response = await client.post("/api/docs/upload", files=files)
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
