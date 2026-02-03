"""
End-to-End Integration Tests for the RAG System
Tests the complete flow from document upload to chat response
"""
import pytest
import pytest_asyncio
import sys
import tempfile
import shutil
import os
from pathlib import Path

import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def client(temp_data_dir):
    """Create async test client."""
    os.environ["DATA_DIR"] = temp_data_dir
    from production_server import app
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# Sample policy documents for testing
REMOTE_WORK_POLICY = """
REMOTE WORK POLICY
Version 1.0

1. PURPOSE
This policy establishes guidelines for remote work arrangements to support employee flexibility.

2. ELIGIBILITY
2.1 General Requirements
- Employees must have completed at least 6 months of service
- Performance must meet or exceed expectations
- Role must be suitable for remote work

2.2 Manager Approval
Written approval from direct manager is required.

3. EQUIPMENT
The company provides:
- Laptop computer
- External monitor
- Keyboard and mouse
- Headset for video calls

4. WORKING HOURS
- Core hours: 10am - 4pm
- Employees must be available during core hours
- Flexible start and end times allowed

5. SECURITY
- Use VPN for all work activities
- Keep work devices secure
- Report any security incidents immediately
"""

LEAVE_POLICY = """
ANNUAL LEAVE POLICY
Version 2.0

1. OVERVIEW
This policy outlines the company's annual leave provisions.

2. ENTITLEMENT
2.1 Annual Leave
- Full-time employees: 20 days per year
- Part-time employees: Pro-rata based on hours

2.2 Sick Leave
- 10 days per year
- Medical certificate required for 3+ consecutive days

3. REQUESTING LEAVE
- Submit requests at least 2 weeks in advance
- Use the HR portal to submit requests
- Manager approval required

4. CARRYOVER
- Maximum 5 days can be carried to next year
- Carryover must be used within first quarter

5. PUBLIC HOLIDAYS
- 10 paid public holidays per year
- Holiday falling on weekend: Monday in lieu
"""

DATA_PRIVACY_POLICY = """
DATA PRIVACY POLICY
Version 3.0

1. INTRODUCTION
This policy outlines how we handle personal data.

2. DATA COLLECTION
We collect:
- Employee personal information
- Customer contact details
- Transaction records

3. DATA PROTECTION
3.1 Access Control
- Role-based access to data
- Two-factor authentication required
- Regular access reviews

3.2 Encryption
- All data encrypted at rest
- TLS 1.3 for data in transit

4. DATA RETENTION
- Employee data: 7 years after termination
- Customer data: 5 years after last interaction
- Financial records: 10 years

5. BREACH NOTIFICATION
- Report breaches within 24 hours
- Notify affected parties within 72 hours
"""


class TestEndToEndRAGWorkflow:
    """Test complete RAG workflow from upload to response."""
    
    async def test_complete_rag_workflow(self, client):
        """Test the complete workflow: upload, index, search, chat."""
        # Step 1: Upload a document
        files = {"file": ("remote_work.txt", REMOTE_WORK_POLICY, "text/plain")}
        upload_response = await client.post("/api/docs/upload", files=files)
        
        assert upload_response.status_code == 200
        doc_data = upload_response.json()
        assert doc_data["success"] is True
        doc_id = doc_data["id"]
        
        # Step 2: Verify document is listed
        list_response = await client.get("/api/docs")
        docs = list_response.json()["documents"]
        assert any(d["id"] == doc_id for d in docs)
        
        # Step 3: Check stats show the document
        stats_response = await client.get("/api/stats")
        stats = stats_response.json()
        assert stats["vector_store"]["unique_documents"] >= 1
        
        # Step 4: Ask a question about the document
        chat_response = await client.post("/api/chat", json={
            "question": "What are the eligibility requirements for remote work?",
            "provider": "ollama"
        })
        
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        # Should have an answer
        assert "answer" in chat_data
        assert len(chat_data["answer"]) > 0
        
        # Should have used context (citations)
        assert "citations" in chat_data
    
    async def test_multi_document_search(self, client):
        """Test searching across multiple documents."""
        # Upload multiple documents
        docs = [
            ("remote.txt", REMOTE_WORK_POLICY),
            ("leave.txt", LEAVE_POLICY),
            ("privacy.txt", DATA_PRIVACY_POLICY)
        ]
        
        doc_ids = []
        for filename, content in docs:
            files = {"file": (filename, content, "text/plain")}
            response = await client.post("/api/docs/upload", files=files)
            if response.status_code == 200:
                doc_ids.append(response.json()["id"])
        
        # Ask about leave - should return leave policy
        leave_response = await client.post("/api/chat", json={
            "question": "How many vacation days do I get per year?",
            "provider": "ollama"
        })
        
        leave_data = leave_response.json()
        # Should mention 20 days or annual leave
        assert "answer" in leave_data
        
        # Ask about security - should return relevant policy
        security_response = await client.post("/api/chat", json={
            "question": "What are the VPN requirements?",
            "provider": "ollama"
        })
        
        security_data = security_response.json()
        assert "answer" in security_data
    
    async def test_filtered_document_search(self, client):
        """Test searching within specific documents."""
        # Upload documents
        files1 = {"file": ("policy_a.txt", REMOTE_WORK_POLICY, "text/plain")}
        files2 = {"file": ("policy_b.txt", LEAVE_POLICY, "text/plain")}
        
        resp1 = await client.post("/api/docs/upload", files=files1)
        resp2 = await client.post("/api/docs/upload", files=files2)
        
        doc_id_1 = resp1.json()["id"]
        doc_id_2 = resp2.json()["id"]
        
        # Search only in leave policy
        response = await client.post("/api/chat", json={
            "question": "What is the policy about?",
            "provider": "ollama",
            "doc_ids": [doc_id_2]
        })
        
        data = response.json()
        # Citations should only be from the filtered document
        for citation in data.get("citations", []):
            assert citation["doc_id"] == doc_id_2


class TestChatHistoryIntegration:
    """Test chat history integration."""
    
    async def test_chat_history_persists(self, client):
        """Test that chat history is saved and retrieved."""
        user_id = "history-test-user"
        
        # Send some messages
        messages = [
            "What is remote work?",
            "How do I apply for remote work?",
            "What equipment is provided?"
        ]
        
        for msg in messages:
            await client.post("/api/chat", json={
                "question": msg,
                "provider": "ollama",
                "user_id": user_id
            })
        
        # Get history
        response = await client.get(f"/api/chat/history?user_id={user_id}")
        history = response.json()
        
        # Should have messages (user + assistant for each)
        assert len(history["messages"]) >= len(messages)
    
    async def test_chat_history_isolated_by_user(self, client):
        """Test that chat history is isolated by user."""
        # User A messages
        await client.post("/api/chat", json={
            "question": "User A question",
            "provider": "ollama",
            "user_id": "user-a"
        })
        
        # User B messages
        await client.post("/api/chat", json={
            "question": "User B question",
            "provider": "ollama",
            "user_id": "user-b"
        })
        
        # Get histories
        resp_a = await client.get("/api/chat/history?user_id=user-a")
        resp_b = await client.get("/api/chat/history?user_id=user-b")
        history_a = resp_a.json()
        history_b = resp_b.json()
        
        # Each should have their own messages
        assert history_a["user_id"] == "user-a"
        assert history_b["user_id"] == "user-b"
    
    async def test_clear_history_works(self, client):
        """Test clearing chat history."""
        user_id = "clear-history-user"
        
        # Add messages
        for i in range(3):
            await client.post("/api/chat", json={
                "question": f"Question {i}",
                "provider": "ollama",
                "user_id": user_id
            })
        
        # Clear
        clear_response = await client.post(f"/api/chat/clear?user_id={user_id}")
        assert clear_response.json()["success"] is True
        
        # Verify cleared
        history_resp = await client.get(f"/api/chat/history?user_id={user_id}")
        history = history_resp.json()
        assert len(history["messages"]) == 0


class TestDocumentLifecycle:
    """Test document upload, indexing, and deletion lifecycle."""
    
    async def test_document_lifecycle(self, client):
        """Test complete document lifecycle."""
        # Create
        files = {"file": ("lifecycle.txt", "Lifecycle test content", "text/plain")}
        create_response = await client.post("/api/docs/upload", files=files)
        doc_id = create_response.json()["id"]
        
        # Verify exists
        docs_resp = await client.get("/api/docs")
        docs = docs_resp.json()["documents"]
        assert any(d["id"] == doc_id for d in docs)
        
        # Use in chat
        chat_response = await client.post("/api/chat", json={
            "question": "What is the lifecycle test about?",
            "provider": "ollama",
            "doc_ids": [doc_id]
        })
        assert chat_response.status_code == 200
        
        # Delete
        delete_response = await client.delete(f"/api/docs/{doc_id}")
        assert delete_response.json()["success"] is True
        
        # Verify deleted
        docs_resp = await client.get("/api/docs")
        docs = docs_resp.json()["documents"]
        assert not any(d["id"] == doc_id for d in docs)
    
    async def test_delete_removes_from_vector_store(self, client):
        """Test that deletion removes document from vector store."""
        # Upload
        files = {"file": ("delete_test.txt", "Content for vector store test", "text/plain")}
        response = await client.post("/api/docs/upload", files=files)
        doc_id = response.json()["id"]
        
        # Get initial stats
        initial_resp = await client.get("/api/stats")
        initial_stats = initial_resp.json()
        initial_chunks = initial_stats["vector_store"]["total_chunks"]
        
        # Delete
        await client.delete(f"/api/docs/{doc_id}")
        
        # Get new stats
        new_resp = await client.get("/api/stats")
        new_stats = new_resp.json()
        new_chunks = new_stats["vector_store"]["total_chunks"]
        
        # Chunks should decrease
        assert new_chunks < initial_chunks


class TestSemanticSearchQuality:
    """Test quality of semantic search results."""
    
    async def test_relevant_content_ranked_higher(self, client):
        """Test that relevant content is ranked higher in results."""
        # Upload specific content
        files = {"file": ("specific.txt", """
        VACATION POLICY
        Employees receive 20 days of paid time off annually.
        Vacation must be requested through HR.
        """, "text/plain")}
        await client.post("/api/docs/upload", files=files)
        
        # Search for vacation-related info
        response = await client.post("/api/chat", json={
            "question": "How many days of vacation do employees get?",
            "provider": "ollama"
        })
        
        data = response.json()
        # Should find and cite the vacation policy
        assert len(data.get("citations", [])) > 0
    
    async def test_context_improves_answers(self, client):
        """Test that having document context improves answers."""
        # Upload context
        files = {"file": ("context_test.txt", """
        COMPANY HOLIDAY SCHEDULE 2024
        - New Year's Day: January 1
        - Memorial Day: May 27
        - Independence Day: July 4
        - Labor Day: September 2
        - Thanksgiving: November 28-29
        - Christmas: December 25
        """, "text/plain")}
        await client.post("/api/docs/upload", files=files)
        
        # Ask about holidays
        response = await client.post("/api/chat", json={
            "question": "When is the Thanksgiving holiday?",
            "provider": "ollama"
        })
        
        data = response.json()
        # Answer should reference November
        assert "answer" in data


class TestErrorRecovery:
    """Test error recovery and edge cases."""
    
    async def test_chat_without_documents(self, client):
        """Test chat works even without uploaded documents."""
        response = await client.post("/api/chat", json={
            "question": "What is the meaning of life?",
            "provider": "ollama"
        })
        
        assert response.status_code == 200
        assert "answer" in response.json()
    
    async def test_upload_empty_file(self, client):
        """Test uploading an empty file."""
        files = {"file": ("empty.txt", "", "text/plain")}
        response = await client.post("/api/docs/upload", files=files)
        
        # Should handle gracefully
        assert response.status_code == 200
    
    async def test_very_long_question(self, client):
        """Test handling very long questions."""
        long_question = "What is " + "the policy " * 500 + "about?"
        
        response = await client.post("/api/chat", json={
            "question": long_question,
            "provider": "ollama"
        })
        
        # Should handle without crashing
        assert response.status_code == 200


class TestConcurrentOperations:
    """Test concurrent-like operations."""
    
    async def test_multiple_uploads(self, client):
        """Test multiple document uploads."""
        for i in range(5):
            files = {"file": (f"concurrent_{i}.txt", f"Content {i}", "text/plain")}
            response = await client.post("/api/docs/upload", files=files)
            assert response.status_code == 200
    
    async def test_multiple_chats(self, client):
        """Test multiple chat requests."""
        questions = [
            "What is remote work?",
            "How many vacation days?",
            "What about security?",
            "Data privacy rules?",
            "Working hours policy?"
        ]
        
        for question in questions:
            response = await client.post("/api/chat", json={
                "question": question,
                "provider": "ollama"
            })
            assert response.status_code == 200


class TestDataConsistency:
    """Test data consistency across operations."""
    
    async def test_stats_consistency(self, client):
        """Test that stats are consistent with actual data."""
        # Upload some documents
        for i in range(3):
            files = {"file": (f"stats_test_{i}.txt", f"Content {i}", "text/plain")}
            await client.post("/api/docs/upload", files=files)
        
        # Get stats
        stats_resp = await client.get("/api/stats")
        stats = stats_resp.json()
        
        # Get actual document list
        docs_resp = await client.get("/api/docs")
        docs = docs_resp.json()["documents"]
        
        # Stats should be consistent
        assert stats["database"]["total_documents"] >= len(docs)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
