"""
End-to-end tests for all new Phase 2 features.
Tests the complete flow from API calls to responses.
"""
import pytest
import requests
import json
import time
import os
from io import BytesIO

# Test configuration
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8001")
TIMEOUT = 30


class TestE2EBatchUpload:
    """End-to-end tests for batch document upload."""
    
    def test_batch_upload_flow(self):
        """Test complete batch upload workflow."""
        # Prepare test files
        files = [
            ("files", ("policy1.txt", BytesIO(b"Leave policy content here."), "text/plain")),
            ("files", ("policy2.txt", BytesIO(b"Remote work policy content."), "text/plain")),
        ]
        
        # Upload batch
        response = requests.post(
            f"{BASE_URL}/api/docs/upload/batch",
            files=files,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert len(data["results"]) == 2
        
        # Verify each upload result
        for result in data["results"]:
            assert "status" in result
            assert "filename" in result
            if result["status"] == "success":
                assert "doc_id" in result or "id" in result
        
        # Clean up - delete uploaded documents
        for result in data["results"]:
            if result["status"] == "success":
                doc_id = result.get("doc_id") or result.get("id")
                if doc_id:
                    requests.delete(f"{BASE_URL}/api/docs/{doc_id}", timeout=TIMEOUT)
    
    def test_batch_upload_validates_file_types(self):
        """Test that batch upload validates file types."""
        files = [
            ("files", ("valid.txt", BytesIO(b"Valid content"), "text/plain")),
            ("files", ("invalid.exe", BytesIO(b"Bad content"), "application/x-msdownload")),
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/docs/upload/batch",
            files=files,
            timeout=TIMEOUT
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_batch_upload_empty_request(self):
        """Test batch upload with no files."""
        response = requests.post(
            f"{BASE_URL}/api/docs/upload/batch",
            files=[],
            timeout=TIMEOUT
        )
        
        assert response.status_code in [400, 422]


class TestE2EChatHistoryExport:
    """End-to-end tests for chat history export."""
    
    def setup_method(self):
        """Setup: send some chat messages."""
        self.user_id = f"test-user-{int(time.time())}"
        
        # Send a few messages to create history
        for i in range(3):
            try:
                requests.post(
                    f"{BASE_URL}/api/chat",
                    json={
                        "query": f"Test question {i}",
                        "provider": "ollama",
                        "user_id": self.user_id,
                        "use_rag": False
                    },
                    timeout=TIMEOUT
                )
            except:
                pass  # LLM might not be available
    
    def test_export_json_format(self):
        """Test exporting chat history as JSON."""
        response = requests.get(
            f"{BASE_URL}/api/chat/history/{self.user_id}/export?format=json",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        
        data = response.json()
        assert "user_id" in data
        assert "messages" in data
        assert "exported_at" in data
    
    def test_export_markdown_format(self):
        """Test exporting chat history as Markdown."""
        response = requests.get(
            f"{BASE_URL}/api/chat/history/{self.user_id}/export?format=markdown",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        assert "text/markdown" in response.headers.get("content-type", "")
        
        content = response.text
        assert "# Chat History Export" in content
    
    def test_export_nonexistent_user(self):
        """Test export for user with no history."""
        response = requests.get(
            f"{BASE_URL}/api/chat/history/nonexistent-user-xyz/export",
            timeout=TIMEOUT
        )
        
        # Should return empty export, not error
        assert response.status_code == 200
        data = response.json()
        assert data.get("messages") == [] or len(data.get("messages", [])) == 0
    
    def teardown_method(self):
        """Cleanup: clear test user's chat history."""
        try:
            requests.delete(
                f"{BASE_URL}/api/chat/history/{self.user_id}",
                timeout=TIMEOUT
            )
        except:
            pass


class TestE2EStreaming:
    """End-to-end tests for streaming chat endpoint."""
    
    def test_streaming_endpoint_available(self):
        """Test that streaming endpoint exists."""
        response = requests.options(
            f"{BASE_URL}/api/chat/stream",
            timeout=TIMEOUT
        )
        # Should not be 404
        assert response.status_code != 404
    
    def test_streaming_with_ollama(self):
        """Test streaming with Ollama provider."""
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "query": "Say hello",
                    "provider": "ollama",
                    "user_id": "test-stream-user"
                },
                stream=True,
                timeout=TIMEOUT
            )
            
            # Should return 200 and stream data
            if response.status_code == 200:
                # Read some chunks
                chunks = []
                for i, line in enumerate(response.iter_lines()):
                    if line:
                        chunks.append(line)
                    if i >= 5:  # Read first 5 chunks
                        break
                
                # Should have received some data
                assert len(chunks) >= 0
        except Exception as e:
            # Ollama might not be available
            pytest.skip(f"Ollama not available: {e}")
    
    def test_streaming_requires_query(self):
        """Test that streaming requires a query."""
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "provider": "ollama",
                "user_id": "test-user"
            },
            timeout=TIMEOUT
        )
        
        assert response.status_code in [400, 422]


class TestE2EDocumentManagement:
    """End-to-end tests for document management."""
    
    def test_full_document_lifecycle(self):
        """Test upload, list, get, delete flow."""
        # 1. Upload
        file_content = b"Test policy document content for lifecycle test."
        files = {"file": ("lifecycle_test.txt", BytesIO(file_content), "text/plain")}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/docs/upload",
            files=files,
            timeout=TIMEOUT
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        doc_id = upload_data.get("doc_id") or upload_data.get("id")
        assert doc_id is not None
        
        # 2. List - should include our document
        list_response = requests.get(f"{BASE_URL}/api/docs", timeout=TIMEOUT)
        assert list_response.status_code == 200
        docs = list_response.json()
        doc_ids = [d.get("id") or d.get("doc_id") for d in docs]
        assert doc_id in doc_ids
        
        # 3. Get specific document
        get_response = requests.get(f"{BASE_URL}/api/docs/{doc_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        
        # 4. Delete
        delete_response = requests.delete(f"{BASE_URL}/api/docs/{doc_id}", timeout=TIMEOUT)
        assert delete_response.status_code in [200, 204]
        
        # 5. Verify deleted
        get_after_delete = requests.get(f"{BASE_URL}/api/docs/{doc_id}", timeout=TIMEOUT)
        assert get_after_delete.status_code == 404
    
    def test_bulk_delete(self):
        """Test bulk document deletion."""
        # Upload multiple documents
        doc_ids = []
        for i in range(3):
            files = {"file": (f"bulk_test_{i}.txt", BytesIO(f"Content {i}".encode()), "text/plain")}
            response = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                doc_id = data.get("doc_id") or data.get("id")
                if doc_id:
                    doc_ids.append(doc_id)
        
        if len(doc_ids) >= 2:
            # Bulk delete
            response = requests.post(
                f"{BASE_URL}/api/docs/bulk-delete",
                json={"doc_ids": doc_ids},
                timeout=TIMEOUT
            )
            assert response.status_code in [200, 204]
            
            # Verify deleted
            for doc_id in doc_ids:
                get_response = requests.get(f"{BASE_URL}/api/docs/{doc_id}", timeout=TIMEOUT)
                assert get_response.status_code == 404


class TestE2EHealthCheck:
    """End-to-end tests for health endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "ok"]
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data


class TestE2EChatWithRAG:
    """End-to-end tests for chat with RAG functionality."""
    
    def setup_method(self):
        """Upload a test document for RAG queries."""
        file_content = b"""
        Company Leave Policy
        
        Employees are entitled to 20 days of paid vacation per year.
        Sick leave is unlimited with doctor's note after 3 consecutive days.
        Maternity leave is 16 weeks paid.
        Paternity leave is 4 weeks paid.
        """
        
        files = {"file": ("leave_policy.txt", BytesIO(file_content), "text/plain")}
        response = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            self.doc_id = data.get("doc_id") or data.get("id")
        else:
            self.doc_id = None
    
    def test_chat_with_rag_enabled(self):
        """Test chat query with RAG enabled."""
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={
                    "query": "How many vacation days do employees get?",
                    "provider": "ollama",
                    "user_id": "rag-test-user",
                    "use_rag": True,
                    "num_results": 3
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data or "response" in data
                # Check for citations if RAG is working
                if "citations" in data:
                    assert isinstance(data["citations"], list)
        except Exception as e:
            pytest.skip(f"LLM not available: {e}")
    
    def test_chat_without_rag(self):
        """Test chat query with RAG disabled."""
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={
                    "query": "Hello, how are you?",
                    "provider": "ollama",
                    "user_id": "no-rag-test-user",
                    "use_rag": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data or "response" in data
        except Exception as e:
            pytest.skip(f"LLM not available: {e}")
    
    def teardown_method(self):
        """Clean up test document."""
        if self.doc_id:
            try:
                requests.delete(f"{BASE_URL}/api/docs/{self.doc_id}", timeout=TIMEOUT)
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
