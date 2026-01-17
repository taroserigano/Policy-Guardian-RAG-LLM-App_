"""
Comprehensive tests for the simple_server.py
Includes unit tests, integration tests, and E2E scenarios
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simple_server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Unit tests for health check endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Test health endpoint returns 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_returns_healthy_status(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "Policy RAG API - Simple Server"


class TestRootEndpoint:
    """Unit tests for root endpoint."""
    
    def test_root_returns_200(self, client):
        """Test root endpoint returns 200 status code."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_api_info(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert data["name"] == "Policy RAG API - Simple Server"


class TestDocumentEndpoints:
    """Unit tests for document management endpoints."""
    
    def test_list_documents_returns_200(self, client):
        """Test document list endpoint returns 200."""
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_list_documents_returns_array(self, client):
        """Test document list returns an array."""
        response = client.get("/api/docs")
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_documents_contains_sample_docs(self, client):
        """Test document list contains pre-loaded sample documents."""
        response = client.get("/api/docs")
        data = response.json()
        assert len(data) >= 4  # Should have at least 4 sample documents
        
        # Check for specific documents
        filenames = [doc["filename"] for doc in data]
        assert "employee_leave_policy.txt" in filenames
        assert "remote_work_policy.txt" in filenames
        assert "data_privacy_policy.txt" in filenames
        assert "non_disclosure_agreement.txt" in filenames
    
    def test_document_structure(self, client):
        """Test document objects have correct structure."""
        response = client.get("/api/docs")
        data = response.json()
        
        for doc in data:
            assert "id" in doc
            assert "filename" in doc
            assert "content_type" in doc
            assert "preview_text" in doc
            assert "size" in doc
    
    def test_upload_document_returns_200(self, client):
        """Test document upload returns 200."""
        file_content = b"This is a test document content."
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        
        response = client.post("/api/docs/upload", files=files)
        assert response.status_code == 200
    
    def test_upload_document_returns_success(self, client):
        """Test document upload returns success and document info."""
        file_content = b"This is a test document content."
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        
        response = client.post("/api/docs/upload", files=files)
        data = response.json()
        
        assert data["success"] == True
        assert "id" in data
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
    
    def test_upload_document_appears_in_list(self, client):
        """Test uploaded document appears in document list."""
        # Upload a document
        file_content = b"New test document"
        files = {"file": ("new_doc.txt", BytesIO(file_content), "text/plain")}
        client.post("/api/docs/upload", files=files)
        
        # Check it appears in list
        response = client.get("/api/docs")
        data = response.json()
        filenames = [doc["filename"] for doc in data]
        assert "new_doc.txt" in filenames


class TestChatEndpointLeavePolicy:
    """Unit tests for chat endpoint - Leave Policy questions."""
    
    def test_chat_endpoint_returns_200(self, client):
        """Test chat endpoint returns 200 status code."""
        response = client.post("/api/chat", json={"question": "test", "user_id": "test-user"})
        assert response.status_code == 200
    
    def test_chat_leave_policy_keyword(self, client):
        """Test chat recognizes 'leave' keyword."""
        response = client.post("/api/chat", json={"question": "tell me about leave policy", "user_id": "test-user"})
        data = response.json()
        
        assert "answer" in data
        assert "citations" in data
        assert "leave" in data["answer"].lower() or "annual" in data["answer"].lower()
    
    def test_chat_leave_policy_uppercase(self, client):
        """Test chat works with uppercase input."""
        response = client.post("/api/chat", json={"question": "TELL ME ABOUT LEAVE POLICY", "user_id": "test-user"})
        data = response.json()
        
        assert response.status_code == 200
        assert "annual leave" in data["answer"].lower()
    
    def test_chat_leave_policy_mixed_case(self, client):
        """Test chat works with mixed case input."""
        response = client.post("/api/chat", json={"question": "Tell Me About LeAvE PoLiCy", "user_id": "test-user"})
        data = response.json()
        
        assert response.status_code == 200
        assert "answer" in data
    
    def test_chat_annual_leave_details(self, client):
        """Test chat provides annual leave details."""
        response = client.post("/api/chat", json={"question": "how many annual leave days?", "user_id": "test-user"})
        data = response.json()
        
        answer = data["answer"]
        assert "20 days" in answer or "20" in answer
        assert "annual" in answer.lower()
    
    def test_chat_sick_leave_details(self, client):
        """Test chat provides sick leave details."""
        response = client.post("/api/chat", json={"question": "what is the sick leave policy?", "user_id": "test-user"})
        data = response.json()
        
        answer = data["answer"]
        assert "10 days" in answer or "10" in answer
        assert "sick" in answer.lower()
    
    def test_chat_parental_leave_details(self, client):
        """Test chat provides parental leave details."""
        response = client.post("/api/chat", json={"question": "what is maternity leave?", "user_id": "test-user"})
        data = response.json()
        
        answer = data["answer"]
        assert "16 weeks" in answer or "maternity" in answer.lower()
        assert "parental" in answer.lower() or "maternity" in answer.lower()
    
    def test_chat_vacation_synonym(self, client):
        """Test chat recognizes 'vacation' as synonym for leave."""
        response = client.post("/api/chat", json={"question": "vacation policy", "user_id": "test-user"})
        data = response.json()
        
        assert "20 days" in data["answer"] or "annual" in data["answer"].lower()
    
    def test_chat_leave_citations(self, client):
        """Test chat returns citations for leave policy."""
        response = client.post("/api/chat", json={"question": "leave policy", "user_id": "test-user"})
        data = response.json()
        
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0
        
        # Check citation structure
        citation = data["citations"][0]
        assert "doc_id" in citation
        assert "filename" in citation
        assert "employee_leave_policy.txt" in citation["filename"].lower()


class TestChatEndpointRemoteWork:
    """Unit tests for chat endpoint - Remote Work Policy questions."""
    
    def test_chat_remote_work_keyword(self, client):
        """Test chat recognizes 'remote' keyword."""
        response = client.post("/api/chat", json={"question": "remote work policy", "user_id": "test-user"})
        data = response.json()
        
        assert "remote" in data["answer"].lower()
        assert "2 days" in data["answer"] or "hybrid" in data["answer"].lower()
    
    def test_chat_work_from_home(self, client):
        """Test chat recognizes 'work from home' phrase."""
        response = client.post("/api/chat", json={"question": "can I work from home?", "user_id": "test-user"})
        data = response.json()
        
        assert "remote" in data["answer"].lower() or "hybrid" in data["answer"].lower()
    
    def test_chat_wfh_abbreviation(self, client):
        """Test chat recognizes 'wfh' abbreviation."""
        response = client.post("/api/chat", json={"question": "wfh policy", "user_id": "test-user"})
        data = response.json()
        
        assert "remote" in data["answer"].lower() or "hybrid" in data["answer"].lower()
    
    def test_chat_remote_work_citations(self, client):
        """Test chat returns remote work policy citations."""
        response = client.post("/api/chat", json={"question": "remote work", "user_id": "test-user"})
        data = response.json()
        
        citations = data["citations"]
        filenames = [c["filename"] for c in citations]
        assert any("remote" in f.lower() for f in filenames)


class TestChatEndpointDataPrivacy:
    """Unit tests for chat endpoint - Data Privacy questions."""
    
    def test_chat_privacy_keyword(self, client):
        """Test chat recognizes 'privacy' keyword."""
        response = client.post("/api/chat", json={"question": "data privacy policy", "user_id": "test-user"})
        data = response.json()
        
        assert "privacy" in data["answer"].lower() or "data" in data["answer"].lower()
    
    def test_chat_gdpr_keyword(self, client):
        """Test chat recognizes 'gdpr' keyword."""
        response = client.post("/api/chat", json={"question": "gdpr compliance", "user_id": "test-user"})
        data = response.json()
        
        assert "data" in data["answer"].lower() or "privacy" in data["answer"].lower()
    
    def test_chat_retention_keyword(self, client):
        """Test chat recognizes 'retention' keyword."""
        response = client.post("/api/chat", json={"question": "data retention period", "user_id": "test-user"})
        data = response.json()
        
        assert "retention" in data["answer"].lower() or "7 years" in data["answer"]


class TestChatEndpointNDA:
    """Unit tests for chat endpoint - NDA questions."""
    
    def test_chat_nda_keyword(self, client):
        """Test chat recognizes 'nda' keyword."""
        response = client.post("/api/chat", json={"question": "nda policy", "user_id": "test-user"})
        data = response.json()
        
        assert "confidential" in data["answer"].lower() or "nda" in data["answer"].lower()
    
    def test_chat_confidential_keyword(self, client):
        """Test chat recognizes 'confidential' keyword."""
        response = client.post("/api/chat", json={"question": "confidential information", "user_id": "test-user"})
        data = response.json()
        
        assert "confidential" in data["answer"].lower()
    
    def test_chat_disclosure_keyword(self, client):
        """Test chat recognizes 'disclosure' keyword."""
        response = client.post("/api/chat", json={"question": "disclosure requirements", "user_id": "test-user"})
        data = response.json()
        
        assert "confidential" in data["answer"].lower() or "disclosure" in data["answer"].lower()


class TestChatEndpointGeneralQueries:
    """Unit tests for chat endpoint - General queries."""
    
    def test_chat_general_query_returns_guidance(self, client):
        """Test chat returns helpful guidance for vague queries."""
        response = client.post("/api/chat", json={"question": "tell me about policy", "user_id": "test-user"})
        data = response.json()
        
        answer = data["answer"]
        # Should mention available documents or suggest specific questions
        assert "policy" in answer.lower()
    
    def test_chat_empty_question_validation(self, client):
        """Test chat validates empty questions."""
        response = client.post("/api/chat", json={"question": ""})
        # Should either return 422 (validation error) or handle gracefully
        assert response.status_code in [200, 422]
    
    def test_chat_response_structure(self, client):
        """Test chat response has correct structure."""
        response = client.post("/api/chat", json={"question": "leave policy", "user_id": "test-user"})
        data = response.json()
        
        assert "answer" in data
        assert "citations" in data
        assert isinstance(data["answer"], str)
        assert isinstance(data["citations"], list)
        assert len(data["answer"]) > 0


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow_upload_and_query(self, client):
        """Test complete workflow: upload document and query it."""
        # Step 1: Upload a document
        file_content = b"Company policy: Employees get 25 days of vacation."
        files = {"file": ("company_policy.txt", BytesIO(file_content), "text/plain")}
        upload_response = client.post("/api/docs/upload", files=files)
        assert upload_response.status_code == 200
        
        # Step 2: Verify document is in list
        list_response = client.get("/api/docs")
        filenames = [doc["filename"] for doc in list_response.json()]
        assert "company_policy.txt" in filenames
        
        # Step 3: Query about the content
        chat_response = client.post("/api/chat", json={"question": "vacation policy", "user_id": "test-user"})
        assert chat_response.status_code == 200
    
    def test_multiple_queries_same_topic(self, client):
        """Test multiple queries about the same topic return consistent info."""
        questions = [
            "leave policy",
            "how many vacation days?",
            "annual leave",
            "time off policy"
        ]
        
        responses = []
        for question in questions:
            response = client.post("/api/chat", json={"question": question})
            assert response.status_code == 200
            responses.append(response.json())
        
        # All should mention 20 days (from sample policy)
        for data in responses:
            answer = data["answer"].lower()
            assert "20" in data["answer"] or "annual" in answer or "leave" in answer


class TestE2EScenarios:
    """End-to-end tests simulating real user scenarios."""
    
    def test_e2e_new_employee_onboarding(self, client):
        """E2E: New employee asking about various policies."""
        scenarios = [
            {
                "question": "How many vacation days do I get?",
                "expected_keywords": ["20", "annual", "leave"]
            },
            {
                "question": "Can I work from home?",
                "expected_keywords": ["remote", "2 days", "hybrid"]
            },
            {
                "question": "What happens if I'm sick?",
                "expected_keywords": ["10", "sick", "leave"]
            },
            {
                "question": "What is the NDA about?",
                "expected_keywords": ["confidential", "disclosure"]
            }
        ]
        
        for scenario in scenarios:
            response = client.post("/api/chat", json={"question": scenario["question"]})
            assert response.status_code == 200
            
            data = response.json()
            answer = data["answer"].lower()
            
            # Check at least one expected keyword is present
            has_keyword = any(keyword.lower() in answer for keyword in scenario["expected_keywords"])
            assert has_keyword, f"Expected keywords {scenario['expected_keywords']} not found in answer for: {scenario['question']}"
    
    def test_e2e_manager_checking_policies(self, client):
        """E2E: Manager looking up multiple policy details."""
        # Check all sample documents are available
        docs_response = client.get("/api/docs")
        assert docs_response.status_code == 200
        docs = docs_response.json()
        assert len(docs) >= 4
        
        # Ask specific questions about each policy
        questions = [
            "What is the sick leave medical certificate requirement?",
            "How many days notice for remote work?",
            "What are the data retention periods?",
            "What are NDA obligations?"
        ]
        
        for question in questions:
            response = client.post("/api/chat", json={"question": question})
            assert response.status_code == 200
            data = response.json()
            assert len(data["answer"]) > 50  # Should be a substantial answer
            assert len(data["citations"]) > 0  # Should have citations
    
    def test_e2e_hr_document_management(self, client):
        """E2E: HR uploading and managing documents."""
        # Upload multiple documents
        docs_to_upload = [
            ("hr_policy_1.txt", b"HR Policy content 1"),
            ("hr_policy_2.txt", b"HR Policy content 2"),
            ("hr_policy_3.txt", b"HR Policy content 3")
        ]
        
        for filename, content in docs_to_upload:
            files = {"file": (filename, BytesIO(content), "text/plain")}
            response = client.post("/api/docs/upload", files=files)
            assert response.status_code == 200
        
        # Verify all documents are listed
        list_response = client.get("/api/docs")
        all_docs = list_response.json()
        uploaded_filenames = [doc["filename"] for doc in all_docs]
        
        for filename, _ in docs_to_upload:
            assert filename in uploaded_filenames


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_chat_with_very_long_question(self, client):
        """Test chat handles very long questions."""
        long_question = "What is the policy for " + "annual leave " * 100
        response = client.post("/api/chat", json={"question": long_question})
        assert response.status_code == 200
    
    def test_chat_with_special_characters(self, client):
        """Test chat handles special characters."""
        response = client.post("/api/chat", json={"question": "What's the leave policy? @#$%", "user_id": "test-user"})
        assert response.status_code == 200
    
    def test_upload_empty_file(self, client):
        """Test uploading empty file."""
        files = {"file": ("empty.txt", BytesIO(b""), "text/plain")}
        response = client.post("/api/docs/upload", files=files)
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_chat_multiple_keywords(self, client):
        """Test chat with multiple policy keywords."""
        response = client.post("/api/chat", json={
            "question": "Tell me about leave, remote work, and data privacy policies"
        })
        assert response.status_code == 200
        data = response.json()
        # Should match at least one keyword
        answer = data["answer"].lower()
        assert any(keyword in answer for keyword in ["leave", "remote", "privacy"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
