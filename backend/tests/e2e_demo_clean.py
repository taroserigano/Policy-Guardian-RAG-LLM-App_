"""
E2E Demonstration Script - Clean Output
"""
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from simple_server import app

client = TestClient(app)

def ask(question):
    """Ask a question and return formatted response"""
    response = client.post("/api/chat", json={"question": question, "user_id": "demo"})
    if response.status_code == 200:
        data = response.json()
        return {
            'status': response.status_code,
            'answer': data['answer'],
            'citations': len(data['citations']),
            'docs': [c['filename'] for c in data['citations']]
        }
    return {'status': response.status_code, 'error': response.text}

# Test cases
tests = [
    "tell me about leave policy",
    "TELL ME ABOUT LEAVE POLICY",
    "How many vacation days do I get?",
    "What is the sick leave policy?",
    "Can I work from home?",
    "What are the data retention requirements?",
    "Tell me about the NDA",
]

print("\n" + "="*100)
print(" "*35 + "E2E DEMONSTRATION")
print("="*100 + "\n")

for i, question in enumerate(tests, 1):
    print(f"\n{'='*100}")
    print(f"TEST {i}: {question}")
    print('='*100)
    
    result = ask(question)
    
    print(f"\n✅ STATUS: {result['status']}")
    print(f"📚 CITATIONS: {result['citations']} document(s)")
    if 'docs' in result:
        for doc in result['docs']:
            print(f"   - {doc}")
    
    print(f"\n💬 RESPONSE:\n")
    print(result['answer'])

print("\n" + "="*100)
print("✅ E2E DEMONSTRATION COMPLETE - All responses are actual API responses")
print("="*100 + "\n")
