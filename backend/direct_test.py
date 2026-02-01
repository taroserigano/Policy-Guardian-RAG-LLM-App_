"""Direct test of the streaming endpoint"""
import requests
import json

# Get doc ID
docs = requests.get("http://localhost:8005/api/docs").json()
doc_id = docs[0]["id"]

print(f"Testing with doc: {doc_id}\n")

# Stream request
payload = {
    "user_id": "test",
    "provider": "openai",
    "question": "What are the dress code requirements?",
    "doc_ids": [doc_id],
    "image_ids": [],
    "top_k": 3
}

response = requests.post(
    "http://localhost:8005/api/chat/stream",
    json=payload,
    stream=True
)

print(f"Status: {response.status_code}\n")

tokens = []
for line in response.iter_lines():
    if line:
        try:
            data = json.loads(line.decode()[6:])  # Remove 'data: '
            if data['type'] == 'token':
                tokens.append(data['data'])
                print(data['data'], end='', flush=True)
            elif data['type'] == 'citations':
                print(f"\n[{len(data['data'])} citations]")
            elif data['type'] == 'error':
                print(f"\nERROR: {data['data']}")
        except:
            pass

print(f"\n\nTotal tokens: {len(tokens)}")
if tokens:
    print("SUCCESS!")
else:
    print("FAILED - NO TOKENS")
