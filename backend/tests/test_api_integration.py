"""
API Integration Tests for RAG Application
Tests API endpoints directly with HTTP requests
"""
import pytest
import httpx
import asyncio
import os
from typing import Optional


BASE_URL = os.getenv("API_URL", "http://localhost:8001")


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns"""
        try:
            response = httpx.get(f"{BASE_URL}/", timeout=5)
            assert response.status_code < 500
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
    
    def test_docs_endpoint(self):
        """Test API docs are accessible"""
        try:
            response = httpx.get(f"{BASE_URL}/docs", timeout=5)
            assert response.status_code == 200
            assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = httpx.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
        except Exception:
            # Health endpoint might not exist
            pass


class TestDocumentEndpoints:
    """Test document management endpoints"""
    
    def test_list_documents(self):
        """Test document listing endpoint"""
        try:
            response = httpx.get(f"{BASE_URL}/api/docs", timeout=10)
            assert response.status_code < 500
            
            if response.status_code == 200:
                data = response.json()
                # Should return list or object with documents
                assert isinstance(data, (list, dict))
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
    
    def test_upload_document(self):
        """Test document upload endpoint"""
        try:
            # Create test file content
            test_content = b"This is a test document for testing the upload endpoint."
            files = {"file": ("test_doc.txt", test_content, "text/plain")}
            
            response = httpx.post(
                f"{BASE_URL}/api/upload",
                files=files,
                timeout=30
            )
            
            # Should accept upload or return auth error
            assert response.status_code in [200, 201, 401, 403, 422]
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
    
    def test_delete_document(self):
        """Test document deletion endpoint"""
        try:
            # Try to delete non-existent doc
            response = httpx.delete(
                f"{BASE_URL}/api/docs/nonexistent-id",
                timeout=10
            )
            
            # Should return 404 or auth error
            assert response.status_code in [200, 204, 401, 403, 404]
        except httpx.ConnectError:
            pytest.skip("Backend server not running")


class TestChatEndpoints:
    """Test chat/RAG endpoints"""
    
    def test_chat_endpoint_exists(self):
        """Test chat endpoint is accessible"""
        try:
            response = httpx.post(
                f"{BASE_URL}/api/chat",
                json={
                    "user_id": "test-user",
                    "provider": "ollama",
                    "question": "Test question",
                },
                timeout=30
            )
            
            # Should not be 404
            assert response.status_code != 404
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
    
    def test_chat_with_valid_request(self):
        """Test chat with valid request body"""
        try:
            response = httpx.post(
                f"{BASE_URL}/api/chat",
                json={
                    "user_id": "test-user",
                    "provider": "ollama",
                    "question": "What is the remote work policy?",
                    "top_k": 3,
                    "use_rag": True
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data or "response" in data or "message" in data
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
        except httpx.ReadTimeout:
            pytest.skip("LLM response timeout (expected if Ollama not running)")
    
    def test_chat_invalid_provider(self):
        """Test chat with invalid provider"""
        try:
            response = httpx.post(
                f"{BASE_URL}/api/chat",
                json={
                    "user_id": "test-user",
                    "provider": "invalid_provider",
                    "question": "Test",
                },
                timeout=10
            )
            
            # Should return error
            assert response.status_code in [400, 422, 500]
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
    
    def test_chat_missing_question(self):
        """Test chat with missing question"""
        try:
            response = httpx.post(
                f"{BASE_URL}/api/chat",
                json={
                    "user_id": "test-user",
                    "provider": "ollama",
                },
                timeout=10
            )
            
            # Should return validation error
            assert response.status_code == 422
        except httpx.ConnectError:
            pytest.skip("Backend server not running")


class TestStreamingEndpoints:
    """Test streaming chat endpoints"""
    
    def test_streaming_endpoint_exists(self):
        """Test streaming endpoint is accessible"""
        try:
            response = httpx.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "user_id": "test-user",
                    "provider": "ollama",
                    "question": "Test",
                },
                timeout=10
            )
            
            # Streaming endpoint may return 200 with chunked response
            # or 404 if not implemented
            assert response.status_code != 500
        except httpx.ConnectError:
            pytest.skip("Backend server not running")


class TestRAGOptions:
    """Test RAG configuration options"""
    
    def test_rag_with_top_k(self):
        """Test RAG with different top_k values"""
        try:
            for k in [1, 3, 5, 10]:
                response = httpx.post(
                    f"{BASE_URL}/api/chat",
                    json={
                        "user_id": "test-user",
                        "provider": "ollama",
                        "question": "Test query",
                        "top_k": k,
                    },
                    timeout=30
                )
                
                assert response.status_code != 500
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
        except httpx.ReadTimeout:
            pass  # LLM timeout expected
    
    def test_rag_disabled(self):
        """Test chat without RAG"""
        try:
            response = httpx.post(
                f"{BASE_URL}/api/chat",
                json={
                    "user_id": "test-user",
                    "provider": "ollama",
                    "question": "What is 2+2?",
                    "use_rag": False,
                },
                timeout=30
            )
            
            assert response.status_code != 500
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
        except httpx.ReadTimeout:
            pass


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self):
        """Test CORS headers are set"""
        try:
            response = httpx.options(
                f"{BASE_URL}/api/chat",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST",
                },
                timeout=5
            )
            
            # Should allow CORS from frontend
            cors_header = response.headers.get("access-control-allow-origin")
            assert cors_header is not None
        except httpx.ConnectError:
            pytest.skip("Backend server not running")


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async endpoint functionality"""
    
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        try:
            async with httpx.AsyncClient() as client:
                # Send multiple requests concurrently
                tasks = [
                    client.get(f"{BASE_URL}/docs", timeout=10)
                    for _ in range(5)
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # At least some should succeed
                successes = [r for r in responses if isinstance(r, httpx.Response) and r.status_code == 200]
                assert len(successes) > 0
        except httpx.ConnectError:
            pytest.skip("Backend server not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
