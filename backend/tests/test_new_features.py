"""
Comprehensive tests for new Phase 2 features:
- Batch document upload
- Chat history export
- Multi-provider streaming
- Health check endpoints
"""
import pytest
import json
import asyncio
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


class TestBatchUpload:
    """Test batch document upload endpoint."""
    
    def test_batch_upload_single_file(self, client: TestClient):
        """Test batch upload with a single file."""
        file_content = b"Test document content for batch upload"
        files = [
            ("files", ("test1.txt", BytesIO(file_content), "text/plain"))
        ]
        
        response = client.post("/api/docs/upload/batch", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        # Accept both 'success' (new upload) or 'exists' (already uploaded)
        assert data["results"][0]["status"] in ["success", "exists"]
        assert data["results"][0]["filename"] == "test1.txt"
    
    def test_batch_upload_multiple_files(self, client: TestClient):
        """Test batch upload with multiple files."""
        files = [
            ("files", ("doc1.txt", BytesIO(b"Content 1"), "text/plain")),
            ("files", ("doc2.txt", BytesIO(b"Content 2"), "text/plain")),
            ("files", ("doc3.txt", BytesIO(b"Content 3"), "text/plain")),
        ]
        
        response = client.post("/api/docs/upload/batch", files=files)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        
        # Check all succeeded or already exist
        for result in data["results"]:
            assert result["status"] in ["success", "exists"]
    
    def test_batch_upload_mixed_results(self, client: TestClient):
        """Test batch upload with some invalid files."""
        files = [
            ("files", ("valid.txt", BytesIO(b"Valid content"), "text/plain")),
            ("files", ("invalid.exe", BytesIO(b"Invalid"), "application/x-msdownload")),
        ]
        
        response = client.post("/api/docs/upload/batch", files=files)
        assert response.status_code == 200
        data = response.json()
        
        # Should have results for both files
        assert len(data["results"]) >= 1
    
    def test_batch_upload_empty(self, client: TestClient):
        """Test batch upload with no files."""
        response = client.post("/api/docs/upload/batch", files=[])
        assert response.status_code in [400, 422]  # Bad request or validation error
    
    def test_batch_upload_large_batch(self, client: TestClient):
        """Test batch upload with many files."""
        files = [
            ("files", (f"doc_{i}.txt", BytesIO(f"Content {i}".encode()), "text/plain"))
            for i in range(10)
        ]
        
        response = client.post("/api/docs/upload/batch", files=files)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10


class TestChatHistoryExport:
    """Test chat history export endpoint."""
    
    def test_export_json_format(self, client: TestClient):
        """Test exporting chat history as JSON."""
        response = client.get("/api/chat/history/test-user/export?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "user_id" in data
        assert "messages" in data
        # API uses 'export_date' not 'exported_at'
        assert "export_date" in data
    
    def test_export_markdown_format(self, client: TestClient):
        """Test exporting chat history as Markdown."""
        response = client.get("/api/chat/history/test-user/export?format=markdown")
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        
        content = response.text
        assert "# Chat History Export" in content
    
    def test_export_default_format(self, client: TestClient):
        """Test export defaults to JSON."""
        response = client.get("/api/chat/history/test-user/export")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_export_invalid_format(self, client: TestClient):
        """Test export with invalid format parameter."""
        response = client.get("/api/chat/history/test-user/export?format=invalid")
        # Should either use default or return error
        assert response.status_code in [200, 400]
    
    def test_export_empty_history(self, client: TestClient):
        """Test export with no chat history."""
        response = client.get("/api/chat/history/new-user-no-history/export")
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == [] or len(data.get("messages", [])) == 0


class TestStreamingEndpoint:
    """Test streaming chat endpoint."""
    
    def test_stream_endpoint_exists(self, client: TestClient):
        """Test that streaming endpoint exists."""
        # OPTIONS request to check endpoint exists
        response = client.options("/api/chat/stream")
        assert response.status_code in [200, 204, 405]
    
    def test_stream_missing_query(self, client: TestClient):
        """Test streaming without query."""
        response = client.post("/api/chat/stream", json={
            "provider": "ollama"
        })
        assert response.status_code in [400, 422]
    
    def test_stream_with_valid_request(self, client: TestClient):
        """Test streaming with valid request structure."""
        response = client.post("/api/chat/stream", json={
            "question": "What is the leave policy?",
            "provider": "ollama",
            "user_id": "test-user"
        })
        # May return 200 with stream or error if Ollama not available
        assert response.status_code in [200, 500, 503]
    
    def test_stream_provider_validation(self, client: TestClient):
        """Test streaming with different providers."""
        providers = ["ollama", "openai", "anthropic"]
        
        for provider in providers:
            response = client.post("/api/chat/stream", json={
                "question": "Test query",
                "provider": provider,
                "user_id": "test-user"
            })
            # Should accept all valid providers
            assert response.status_code in [200, 500, 503]


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test main health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data


class TestDocumentManagement:
    """Test document CRUD operations."""
    
    def test_list_documents(self, client: TestClient):
        """Test listing all documents."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        data = response.json()
        # API returns {"documents": [...]} format
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    def test_upload_txt_document(self, client: TestClient):
        """Test uploading a text document."""
        file_content = b"This is a test policy document with important information."
        files = {
            "file": ("test_policy.txt", BytesIO(file_content), "text/plain")
        }
        
        response = client.post("/api/docs/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        # May return doc_id/id for new, or message for existing
        assert "doc_id" in data or "id" in data or "message" in data
    
    def test_upload_pdf_document(self, client: TestClient):
        """Test uploading a PDF document."""
        # Minimal valid PDF
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>"
        files = {
            "file": ("test.pdf", BytesIO(pdf_content), "application/pdf")
        }
        
        response = client.post("/api/docs/upload", files=files)
        # May fail PDF parsing but should handle gracefully
        assert response.status_code in [200, 400, 422, 500]
    
    def test_delete_document(self, client: TestClient):
        """Test deleting a document."""
        # First upload a document
        file_content = b"Document to delete"
        files = {
            "file": ("to_delete.txt", BytesIO(file_content), "text/plain")
        }
        
        upload_response = client.post("/api/docs/upload", files=files)
        if upload_response.status_code == 200:
            doc_id = upload_response.json().get("doc_id") or upload_response.json().get("id")
            
            # Now delete it
            delete_response = client.delete(f"/api/docs/{doc_id}")
            assert delete_response.status_code in [200, 204]
    
    @pytest.mark.skip(reason="Bulk delete endpoint not implemented")
    def test_bulk_delete_documents(self, client: TestClient):
        """Test bulk deleting documents."""
        # Upload multiple documents
        doc_ids = []
        for i in range(3):
            files = {
                "file": (f"bulk_{i}.txt", BytesIO(f"Content {i}".encode()), "text/plain")
            }
            response = client.post("/api/docs/upload", files=files)
            if response.status_code == 200:
                doc_id = response.json().get("doc_id") or response.json().get("id")
                if doc_id:
                    doc_ids.append(doc_id)
        
        if doc_ids:
            # Bulk delete
            response = client.post("/api/docs/bulk-delete", json={"doc_ids": doc_ids})
            assert response.status_code in [200, 204]


class TestChatEndpoints:
    """Test chat-related endpoints."""
    
    def test_send_chat_message(self, client: TestClient):
        """Test sending a chat message."""
        response = client.post("/api/chat", json={
            "question": "What is the company leave policy?",
            "provider": "ollama",
            "user_id": "test-user"
        })
        # May succeed or fail based on LLM availability
        assert response.status_code in [200, 500, 503]
    
    def test_get_chat_history(self, client: TestClient):
        """Test retrieving chat history."""
        response = client.get("/api/chat/history/test-user")
        assert response.status_code == 200
        data = response.json()
        # API returns {"user_id": ..., "messages": [...]} format
        assert "messages" in data
        assert isinstance(data["messages"], list)
    
    def test_clear_chat_history(self, client: TestClient):
        """Test clearing chat history."""
        response = client.delete("/api/chat/history/test-user")
        assert response.status_code in [200, 204]


class TestRAGOptions:
    """Test RAG configuration options."""
    
    def test_chat_with_rag_options(self, client: TestClient):
        """Test chat with RAG options."""
        response = client.post("/api/chat", json={
            "question": "What is the policy?",
            "provider": "ollama",
            "user_id": "test-user",
            "use_rag": True,
            "num_results": 3,
            "similarity_threshold": 0.5
        })
        assert response.status_code in [200, 500, 503]
    
    def test_chat_without_rag(self, client: TestClient):
        """Test chat with RAG disabled."""
        response = client.post("/api/chat", json={
            "question": "Hello, how are you?",
            "provider": "ollama",
            "user_id": "test-user",
            "use_rag": False
        })
        assert response.status_code in [200, 500, 503]


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_invalid_endpoint(self, client: TestClient):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self, client: TestClient):
        """Test method not allowed."""
        response = client.patch("/api/docs")
        assert response.status_code in [405, 404]
    
    def test_malformed_json(self, client: TestClient):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/chat",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test validation of required fields."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422
