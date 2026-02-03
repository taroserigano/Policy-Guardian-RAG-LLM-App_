"""
End-to-End Workflow Tests
Simulates real user scenarios from document upload to Q&A
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
from io import BytesIO
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simple_server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_policy_doc():
    """Create a sample policy document."""
    content = """
COMPANY EXPENSE POLICY

1. GENERAL GUIDELINES
All business expenses must be reasonable, necessary, and properly documented.

2. REIMBURSEMENT LIMITS
- Meals: $50 per day domestic, $75 international
- Hotels: $200 per night domestic, $300 international
- Mileage: $0.65 per mile
- Parking: Actual cost with receipt

3. APPROVAL PROCESS
Expenses under $500: Manager approval
Expenses over $500: Director approval
Expenses over $5000: VP approval

4. SUBMISSION TIMELINE
All expenses must be submitted within 30 days of incurrence.
Reimbursement processed within 14 business days.

5. PROHIBITED EXPENSES
- Personal entertainment
- Alcoholic beverages (unless client entertainment)
- First class airfare (unless over 6 hours)
- Spouse/family travel
    """
    return content.encode('utf-8')


class TestDocumentUploadWorkflow:
    """Test complete document upload workflows."""
    
    def test_upload_single_document_workflow(self, client, sample_policy_doc):
        """Test uploading a single document and verifying it's stored."""
        # Step 1: Upload document
        files = {"file": ("expense_policy.txt", BytesIO(sample_policy_doc), "text/plain")}
        upload_response = client.post("/api/docs/upload", files=files)
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["success"] == True
        assert "id" in upload_data
        doc_id = upload_data["id"]
        
        # Step 2: Verify document in list
        list_response = client.get("/api/docs")
        assert list_response.status_code == 200
        docs = list_response.json()
        
        uploaded_doc = next((d for d in docs if d["id"] == doc_id), None)
        assert uploaded_doc is not None
        assert uploaded_doc["filename"] == "expense_policy.txt"
        assert uploaded_doc["size"] > 0
    
    def test_upload_multiple_documents_workflow(self, client):
        """Test uploading multiple documents in sequence."""
        documents = [
            ("policy1.txt", b"Policy 1 content"),
            ("policy2.txt", b"Policy 2 content"),
            ("policy3.txt", b"Policy 3 content"),
        ]
        
        uploaded_ids = []
        
        # Upload all documents
        for filename, content in documents:
            files = {"file": (filename, BytesIO(content), "text/plain")}
            response = client.post("/api/docs/upload", files=files)
            assert response.status_code == 200
            uploaded_ids.append(response.json()["id"])
        
        # Verify all are in the list
        list_response = client.get("/api/docs")
        docs = list_response.json()
        doc_ids = [d["id"] for d in docs]
        
        for doc_id in uploaded_ids:
            assert doc_id in doc_ids


class TestQueryWorkflow:
    """Test complete query workflows."""
    
    def test_simple_query_workflow(self, client):
        """Test a simple query about pre-loaded documents."""
        # Query about leave policy
        response = client.post("/api/chat", json={
            "question": "How many vacation days do employees get?",
            "provider": "ollama",
            "user_id": "workflow-user-1"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "answer" in data
        assert "citations" in data
        assert "model" in data
        assert len(data["answer"]) > 0
        assert len(data["citations"]) > 0
        
        # Verify citations have correct structure
        citation = data["citations"][0]
        assert "doc_id" in citation
        assert "filename" in citation
        assert "text" in citation
    
    def test_follow_up_query_workflow(self, client):
        """Test a conversation with follow-up questions."""
        user_id = "workflow-user-follow-up"
        
        # First question
        response1 = client.post("/api/chat", json={
            "question": "What is the remote work policy?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert response1.status_code == 200
        
        # Follow-up question (should have context)
        response2 = client.post("/api/chat", json={
            "question": "How many days per week can I do that?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["answer"]) > 0


class TestUploadAndQueryWorkflow:
    """Test combined upload and query workflows."""
    
    def test_upload_then_query_workflow(self, client, sample_policy_doc):
        """Test uploading a document and then querying it."""
        user_id = "upload-query-user"
        
        # Step 1: Upload document
        files = {"file": ("expense_policy.txt", BytesIO(sample_policy_doc), "text/plain")}
        upload_response = client.post("/api/docs/upload", files=files)
        assert upload_response.status_code == 200
        
        # Step 2: Query about the uploaded document
        response = client.post("/api/chat", json={
            "question": "What are the meal reimbursement limits?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should provide an answer
        assert len(data["answer"]) > 0
        assert len(data["citations"]) > 0
    
    def test_upload_query_upload_query_workflow(self, client):
        """Test alternating upload and query operations."""
        user_id = "alternate-user"
        
        # Upload first document
        files1 = {"file": ("doc1.txt", BytesIO(b"Document 1 about vacation policy"), "text/plain")}
        upload1 = client.post("/api/docs/upload", files=files1)
        assert upload1.status_code == 200
        
        # Query
        query1 = client.post("/api/chat", json={
            "question": "vacation policy",
            "provider": "ollama",
            "user_id": user_id
        })
        assert query1.status_code == 200
        
        # Upload second document
        files2 = {"file": ("doc2.txt", BytesIO(b"Document 2 about sick leave policy"), "text/plain")}
        upload2 = client.post("/api/docs/upload", files=files2)
        assert upload2.status_code == 200
        
        # Query again
        query2 = client.post("/api/chat", json={
            "question": "sick leave policy",
            "provider": "ollama",
            "user_id": user_id
        })
        assert query2.status_code == 200


class TestMultiUserWorkflow:
    """Test multiple users using the system simultaneously."""
    
    def test_two_users_independent_sessions(self, client):
        """Test two users with independent conversation sessions."""
        # User 1 asks about leave
        response1a = client.post("/api/chat", json={
            "question": "Tell me about annual leave",
            "provider": "ollama",
            "user_id": "user-1"
        })
        assert response1a.status_code == 200
        
        # User 2 asks about remote work
        response2a = client.post("/api/chat", json={
            "question": "Tell me about remote work",
            "provider": "ollama",
            "user_id": "user-2"
        })
        assert response2a.status_code == 200
        
        # User 1 follow-up (should be about leave)
        response1b = client.post("/api/chat", json={
            "question": "How do I request it?",
            "provider": "ollama",
            "user_id": "user-1"
        })
        assert response1b.status_code == 200
        
        # User 2 follow-up (should be about remote work)
        response2b = client.post("/api/chat", json={
            "question": "What equipment do I get?",
            "provider": "ollama",
            "user_id": "user-2"
        })
        assert response2b.status_code == 200
    
    def test_multiple_users_uploading_documents(self, client):
        """Test multiple users uploading documents concurrently."""
        users = ["user-a", "user-b", "user-c"]
        
        for i, user in enumerate(users):
            # Each user uploads a document
            content = f"User {user} policy document content {i}".encode()
            files = {"file": (f"{user}_policy.txt", BytesIO(content), "text/plain")}
            response = client.post("/api/docs/upload", files=files)
            assert response.status_code == 200
        
        # Verify all documents are in the list
        list_response = client.get("/api/docs")
        docs = list_response.json()
        filenames = [d["filename"] for d in docs]
        
        for user in users:
            assert f"{user}_policy.txt" in filenames


class TestProviderSwitchingWorkflow:
    """Test switching between different LLM providers."""
    
    def test_switch_provider_mid_conversation(self, client):
        """Test switching LLM provider during a conversation."""
        user_id = "provider-switch-user"
        
        # Start with Ollama
        response1 = client.post("/api/chat", json={
            "question": "What is the leave policy?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert response1.status_code == 200
        assert response1.json()["model"]["provider"] == "ollama"
        
        # Switch to OpenAI
        response2 = client.post("/api/chat", json={
            "question": "Tell me more about that",
            "provider": "openai",
            "user_id": user_id
        })
        assert response2.status_code == 200
        assert response2.json()["model"]["provider"] == "openai"
        
        # Switch to Anthropic
        response3 = client.post("/api/chat", json={
            "question": "How do I apply?",
            "provider": "anthropic",
            "user_id": user_id
        })
        assert response3.status_code == 200
        assert response3.json()["model"]["provider"] == "anthropic"
    
    def test_different_users_different_providers(self, client):
        """Test different users using different providers simultaneously."""
        # User 1 with Ollama
        response1 = client.post("/api/chat", json={
            "question": "vacation policy",
            "provider": "ollama",
            "user_id": "user-ollama"
        })
        assert response1.status_code == 200
        
        # User 2 with OpenAI
        response2 = client.post("/api/chat", json={
            "question": "remote work policy",
            "provider": "openai",
            "user_id": "user-openai"
        })
        assert response2.status_code == 200
        
        # User 3 with Anthropic
        response3 = client.post("/api/chat", json={
            "question": "data privacy policy",
            "provider": "anthropic",
            "user_id": "user-anthropic"
        })
        assert response3.status_code == 200


class TestCompleteUserJourney:
    """Test complete user journeys from start to finish."""
    
    def test_new_employee_onboarding_journey(self, client):
        """Test a new employee learning about company policies."""
        user_id = "new-employee-123"
        
        # Step 1: Check available documents
        docs_response = client.get("/api/docs")
        assert docs_response.status_code == 200
        docs = docs_response.json()
        assert len(docs) >= 4  # Sample documents should be available
        
        # Step 2: Ask about leave policy
        leave_response = client.post("/api/chat", json={
            "question": "How much vacation time do I get as a new employee?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert leave_response.status_code == 200
        leave_data = leave_response.json()
        assert "20" in leave_data["answer"] or "annual" in leave_data["answer"].lower()
        
        # Step 3: Ask about sick leave
        sick_response = client.post("/api/chat", json={
            "question": "What if I get sick?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert sick_response.status_code == 200
        
        # Step 4: Ask about remote work
        remote_response = client.post("/api/chat", json={
            "question": "Can I work from home?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert remote_response.status_code == 200
        remote_data = remote_response.json()
        assert "remote" in remote_data["answer"].lower() or "hybrid" in remote_data["answer"].lower()
    
    def test_hr_manager_workflow(self, client, sample_policy_doc):
        """Test an HR manager uploading and querying documents."""
        user_id = "hr-manager-001"
        
        # Step 1: Upload new policy document
        files = {"file": ("new_expense_policy.txt", BytesIO(sample_policy_doc), "text/plain")}
        upload_response = client.post("/api/docs/upload", files=files)
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["id"]
        
        # Step 2: Verify document is accessible
        list_response = client.get("/api/docs")
        docs = list_response.json()
        assert any(d["id"] == doc_id for d in docs)
        
        # Step 3: Query the new document
        query_response = client.post("/api/chat", json={
            "question": "What are the expense reimbursement limits?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert query_response.status_code == 200
        
        # Step 4: Ask follow-up questions
        followup_response = client.post("/api/chat", json={
            "question": "What is the approval process?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert followup_response.status_code == 200
    
    def test_employee_comparing_policies(self, client):
        """Test an employee comparing different policies."""
        user_id = "compare-user"
        
        # Ask about leave policy
        leave_q = client.post("/api/chat", json={
            "question": "What is the leave policy?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert leave_q.status_code == 200
        
        # Ask about remote work
        remote_q = client.post("/api/chat", json={
            "question": "What is the remote work policy?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert remote_q.status_code == 200
        
        # Compare both
        compare_q = client.post("/api/chat", json={
            "question": "Which policy is more flexible?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert compare_q.status_code == 200


class TestErrorRecoveryWorkflow:
    """Test workflows with error conditions and recovery."""
    
    def test_upload_failure_recovery(self, client):
        """Test recovering from an upload failure."""
        # Try to upload with no file (should fail or handle gracefully)
        response1 = client.post("/api/docs/upload")
        # Should either reject or handle gracefully
        assert response1.status_code in [200, 400, 422]
        
        # Successful upload after failure
        files = {"file": ("recovery.txt", BytesIO(b"Recovery document"), "text/plain")}
        response2 = client.post("/api/docs/upload", files=files)
        assert response2.status_code == 200
    
    def test_query_with_invalid_provider(self, client):
        """Test query with invalid provider falls back gracefully."""
        response = client.post("/api/chat", json={
            "question": "test",
            "provider": "invalid-provider",
            "user_id": "test-user"
        })
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestPerformanceWorkflow:
    """Test performance under various conditions."""
    
    def test_rapid_queries(self, client):
        """Test handling rapid successive queries."""
        user_id = "rapid-user"
        questions = [
            "leave policy",
            "remote work",
            "data privacy",
            "nda",
            "vacation days"
        ]
        
        for question in questions:
            response = client.post("/api/chat", json={
                "question": question,
                "provider": "ollama",
                "user_id": user_id
            })
            assert response.status_code == 200
    
    def test_long_conversation(self, client):
        """Test a long conversation with many exchanges."""
        user_id = "long-conversation-user"
        
        # Have a 10-message conversation
        for i in range(10):
            response = client.post("/api/chat", json={
                "question": f"Question {i} about policies",
                "provider": "ollama",
                "user_id": user_id
            })
            assert response.status_code == 200
            assert len(response.json()["answer"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
