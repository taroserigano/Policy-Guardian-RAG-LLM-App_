"""
Test document-only queries (no images)
"""
import requests
import json

BASE_URL = "http://localhost:8003"

# Get documents
print("=== Getting documents ===")
docs_response = requests.get(f"{BASE_URL}/api/docs")
if docs_response.status_code == 200:
    docs = docs_response.json()
    if docs:
        doc_id = docs[0]["id"]
        doc_name = docs[0]["filename"]
        print(f"Using document: {doc_name} ({doc_id})")
    else:
        print("No documents found!")
        exit(1)
else:
    print(f"Failed to get documents: {docs_response.status_code}")
    exit(1)

# Test document-only query
print("\n=== Testing document-only query ===")
query_payload = {
    "user_id": "test-doc-only",
    "provider": "openai",
    "question": "What are the specific dress code requirements for professional office areas?",
    "doc_ids": [doc_id],
    "image_ids": [],  # No images
    "top_k": 3
}

print(f"Payload: {json.dumps(query_payload, indent=2)}")

response = requests.post(
    f"{BASE_URL}/api/chat/stream",
    json=query_payload,
    stream=True,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    events_received = {"token": 0, "citations": 0, "done": 0, "error": 0}
    full_response = ""
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]  # Remove 'data: ' prefix
                try:
                    event = json.loads(data_str)
                    event_type = event.get('type')
                    
                    if event_type == 'token':
                        token = event.get('data', '')
                        full_response += token
                        events_received['token'] += 1
                    elif event_type == 'citations':
                        citations = event.get('data', [])
                        events_received['citations'] = len(citations)
                        print(f"\nCitations: {len(citations)}")
                    elif event_type == 'done':
                        events_received['done'] += 1
                    elif event_type == 'error':
                        error_msg = event.get('data', '')
                        events_received['error'] += 1
                        print(f"\nERROR: {error_msg}")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {data_str[:100]}")
    
    print(f"\nEvents received: {events_received}")
    print(f"Response length: {len(full_response)} chars")
    print(f"\nResponse preview:\n{full_response[:500]}")
    
    if events_received['token'] == 0:
        print("\nEMPTY RESPONSE - NO TOKENS RECEIVED!")
    else:
        print(f"\nSUCCESS - Received {events_received['token']} tokens")
else:
    print(f"Request failed: {response.text}")
