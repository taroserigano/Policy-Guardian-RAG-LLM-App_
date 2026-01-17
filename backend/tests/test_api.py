"""
Test API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO

from app.db.models import Document


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self, client: TestClient):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestDocumentEndpoints:
    """Test document management endpoints."""
    
    def test_list_documents_empty(self, client: TestClient, db: Session):
        """Test listing documents when none exist."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_documents_with_data(self, client: TestClient, db: Session):
        """Test listing documents with existing data."""
        # Create test document
        doc = Document(
            id="test-id-1",
            filename="test.pdf",
            content_type="application/pdf",
            preview_text="Test preview"
        )
        db.add(doc)
        db.commit()
        
        response = client.get("/api/docs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == "test.pdf"
        assert data[0]["id"] == "test-id-1"
    
    def test_get_document_by_id(self, client: TestClient, db: Session):
        """Test retrieving a specific document."""
        # Create test document
        doc = Document(
            id="test-id-2",
            filename="policy.pdf",
            content_type="application/pdf"
        )
        db.add(doc)
        db.commit()
        
        response = client.get("/api/docs/test-id-2")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-id-2"
        assert data["filename"] == "policy.pdf"
    
    def test_get_document_not_found(self, client: TestClient):
        """Test retrieving non-existent document."""
        response = client.get("/api/docs/non-existent-id")
        assert response.status_code == 404


class TestDocumentUpload:
    """Test document upload functionality."""
    
    def test_upload_invalid_file_type(self, client: TestClient):
        """Test uploading invalid file type."""
        # Create a fake .exe file
        file_content = b"fake exe content"
        files = {
            "file": ("malware.exe", BytesIO(file_content), "application/x-msdownload")
        }
        
        response = client.post("/api/docs/upload", files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_empty_filename(self, client: TestClient):
        """Test uploading file with empty name."""
        file_content = b"test content"
        files = {
            "file": ("", BytesIO(file_content), "application/pdf")
        }
        
        response = client.post("/api/docs/upload", files=files)
        assert response.status_code == 400


class TestChatEndpoint:
    """Test chat endpoint."""
    
    def test_chat_invalid_provider(self, client: TestClient):
        """Test chat with invalid provider."""
        request_data = {
            "user_id": "test-user",
            "provider": "invalid_provider",
            "question": "What is the policy?"
        }
        
        response = client.post("/api/chat", json=request_data)
        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]
    
    def test_chat_missing_question(self, client: TestClient):
        """Test chat without question."""
        request_data = {
            "user_id": "test-user",
            "provider": "ollama"
        }
        
        response = client.post("/api/chat", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_chat_valid_request_structure(self, client: TestClient):
        """Test chat request validation passes."""
        request_data = {
            "user_id": "test-user",
            "provider": "ollama",
            "question": "What is the policy?",
            "top_k": 5
        }
        
        # This will fail with actual execution (no Ollama/Pinecone)
        # but we're testing request validation
        response = client.post("/api/chat", json=request_data)
        # Should be either 400 (config error) or 500 (execution error), not 422 (validation error)
        assert response.status_code in [400, 500]
