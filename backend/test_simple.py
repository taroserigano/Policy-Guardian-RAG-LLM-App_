"""Minimal test - just show what's happening"""
import requests
import json

# Use existing server
response = requests.get("http://localhost:8006/api/docs")
doc_id = response.json()[0]["id"]
print(f"Testing with doc: {doc_id}")

# Make streaming request
payload = {
    "user_id": "test",
    "provider": "openai",
    "question": "What are the dress code requirements?",
    "doc_ids": [doc_id],
    "image_ids": [],
    "top_k": 3
}

print("\nSending request...")
r = requests.post(
    "http://localhost:8006/api/chat/stream",
    json=payload,
    stream=True
)

print(f"Status: {r.status_code}\n")

tokens = 0
for line in r.iter_lines():
    if line:
        try:
            data = json.loads(line.decode('utf-8')[6:])  # Remove 'data: '
            if data['type'] == 'token':
                tokens += 1
                print(data['data'], end='', flush=True)
            elif data['type'] == 'citations':
                print(f"\n[Got {len(data['data'])} citations]")
            elif data['type'] == 'error':
                print(f"\nERROR: {data['data']}")
        except:
            pass

print(f"\n\nTotal tokens: {tokens}")
