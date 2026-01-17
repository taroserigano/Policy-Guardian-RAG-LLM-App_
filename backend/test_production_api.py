"""Test the production server API endpoints"""
import requests
import json

BASE_URL = "http://localhost:8002"

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_stats():
    """Test stats endpoint."""
    response = requests.get(f"{BASE_URL}/api/stats")
    print(f"\nStats: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_upload():
    """Test document upload."""
    content = """Remote Work Policy

1. INTRODUCTION
This policy outlines the guidelines for remote work arrangements.

2. ELIGIBILITY
All full-time employees are eligible for remote work.

3. EQUIPMENT
The company provides necessary equipment for remote work.

4. WORKING HOURS
Remote employees must be available during core hours 10am-4pm."""
    
    files = {"file": ("remote_work_policy.txt", content, "text/plain")}
    response = requests.post(f"{BASE_URL}/api/docs/upload", files=files)
    print(f"\nUpload: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json() if response.status_code == 200 else None

def test_docs_list():
    """Test document list."""
    response = requests.get(f"{BASE_URL}/api/docs")
    print(f"\nDocs List: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_chat(question: str):
    """Test chat endpoint."""
    data = {
        "question": question,
        "provider": "ollama",
        "model": "llama3.1:8b"
    }
    response = requests.post(f"{BASE_URL}/api/chat", json=data)
    print(f"\nChat: {response.status_code}")
    result = response.json()
    print(f"Answer: {result.get('answer', 'No answer')[:500]}")
    if result.get('citations'):
        print(f"Citations: {len(result['citations'])} found")
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing Production Server API")
    print("="*50)
    
    try:
        test_health()
        test_stats()
        
        # Upload a document
        upload_result = test_upload()
        
        # List documents
        test_docs_list()
        
        # Test chat
        test_chat("What is the remote work policy about eligibility?")
        
        print("\n" + "="*50)
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Is it running on port 8002?")
    except Exception as e:
        print(f"ERROR: {e}")
