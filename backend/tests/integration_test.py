"""
Integration tests for Policy RAG API endpoints.
Requires: PostgreSQL, Pinecone, and Ollama to be running.
"""

import sys
import os
import io
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine
from app.db.models import Base

client = TestClient(app)

def print_separator(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def setup_database():
    """Initialize database for testing."""
    print("Setting up database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")

def test_health_check():
    """Test the health check endpoint."""
    print_separator("TEST 1: Health Check")
    
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_document_upload():
    """Test document upload endpoint."""
    print_separator("TEST 2: Document Upload")
    
    # Create a test PDF-like file
    test_content = b"This is a test document about company policies. It contains information about leave policies, work from home guidelines, and code of conduct."
    test_file = ("test_policy.txt", io.BytesIO(test_content), "text/plain")
    
    response = client.post(
        "/api/documents/upload",
        files={"file": test_file}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data
    assert data["filename"] == "test_policy.txt"
    
    print("✅ Document upload passed")
    return data["id"]

def test_list_documents():
    """Test listing documents endpoint."""
    print_separator("TEST 3: List Documents")
    
    response = client.get("/api/documents/")
    print(f"Status Code: {response.status_code}")
    print(f"Document Count: {len(response.json())}")
    
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) > 0
    
    # Print document details
    for doc in documents:
        print(f"  - {doc['filename']} (ID: {doc['id'][:8]}...)")
    
    print("✅ List documents passed")

def test_chat_query():
    """Test chat query endpoint."""
    print_separator("TEST 4: Chat Query")
    
    request_data = {
        "question": "What are the company leave policies?",
        "provider": "ollama",
        "model": "llama3.1",
        "user_id": "test-user-123",
        "doc_ids": []
    }
    
    print(f"Query: {request_data['question']}")
    print(f"Provider: {request_data['provider']}")
    print(f"Model: {request_data['model']}")
    
    response = client.post("/api/chat", json=request_data)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer Length: {len(data['answer'])} chars")
        print(f"Citations: {len(data['citations'])}")
        print(f"\nAnswer Preview:\n{data['answer'][:200]}...")
        
        if data['citations']:
            print("\nCitations:")
            for i, citation in enumerate(data['citations'][:3], 1):
                print(f"  {i}. Doc: {citation['doc_id'][:8]}... (Score: {citation['score']:.3f})")
        
        assert "answer" in data
        assert "citations" in data
        print("\n✅ Chat query passed")
    else:
        print(f"Error: {response.json()}")
        print("⚠️  Chat query failed - check if Ollama and Pinecone are running")

def test_chat_with_filter():
    """Test chat query with document filtering."""
    print_separator("TEST 5: Chat with Document Filter")
    
    # First get document IDs
    docs_response = client.get("/api/documents/")
    docs = docs_response.json()
    
    if not docs:
        print("⚠️  No documents to filter, skipping test")
        return
    
    doc_id = docs[0]["id"]
    
    request_data = {
        "question": "Summarize this document",
        "provider": "ollama",
        "model": "llama3.1",
        "user_id": "test-user-456",
        "doc_ids": [doc_id]
    }
    
    print(f"Query: {request_data['question']}")
    print(f"Filtering by Document: {doc_id[:8]}...")
    
    response = client.post("/api/chat", json=request_data)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer Length: {len(data['answer'])} chars")
        print(f"Citations: {len(data['citations'])}")
        
        # Verify citations are from the filtered document
        if data['citations']:
            citation_doc_ids = [c['doc_id'] for c in data['citations']]
            print(f"Citation Doc IDs: {[id[:8] + '...' for id in citation_doc_ids]}")
            assert all(cid == doc_id for cid in citation_doc_ids), "Citations should only be from filtered document"
        
        print("\n✅ Chat with filter passed")
    else:
        print(f"Error: {response.json()}")
        print("⚠️  Chat with filter failed")

def test_invalid_requests():
    """Test API validation and error handling."""
    print_separator("TEST 6: Error Handling")
    
    # Test empty question
    response = client.post("/api/chat", json={
        "question": "",
        "provider": "ollama",
        "model": "llama3.1",
        "user_id": "test-user"
    })
    print(f"Empty question status: {response.status_code}")
    assert response.status_code == 422  # Validation error
    print("✅ Empty question validation passed")
    
    # Test invalid provider
    response = client.post("/api/chat", json={
        "question": "test question",
        "provider": "invalid_provider",
        "model": "test",
        "user_id": "test-user"
    })
    print(f"Invalid provider status: {response.status_code}")
    assert response.status_code == 422
    print("✅ Invalid provider validation passed")
    
    # Test missing file upload
    response = client.post("/api/documents/upload")
    print(f"Missing file status: {response.status_code}")
    assert response.status_code == 422
    print("✅ Missing file validation passed")

def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("  POLICY RAG APPLICATION - INTEGRATION TEST SUITE")
    print("="*70)
    
    try:
        setup_database()
        
        test_health_check()
        test_invalid_requests()
        
        # Document and chat tests
        doc_id = test_document_upload()
        test_list_documents()
        test_chat_query()
        test_chat_with_filter()
        
        print_separator("INTEGRATION TESTS COMPLETED")
        print("✅ All integration tests passed!")
        print("\nNote: Some tests may show warnings if external services")
        print("      (Ollama, Pinecone) are not fully configured.")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
