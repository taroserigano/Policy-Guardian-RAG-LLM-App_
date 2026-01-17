"""
E2E Demonstration - Shows actual questions and responses
"""
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from simple_server import app

client = TestClient(app)

def print_separator():
    print("\n" + "="*80 + "\n")

def test_chat(question):
    """Send a question and display the response."""
    print(f"❓ QUESTION: {question}")
    print("-" * 80)
    
    response = client.post("/api/chat", json={
        "question": question,
        "user_id": "demo-user"
    })
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "")
        citations = data.get("citations", [])
        
        print(f"✅ STATUS: {response.status_code} OK")
        print(f"\n💬 ANSWER:\n{answer}")
        
        if citations:
            print(f"\n📚 CITATIONS ({len(citations)}):")
            for i, cite in enumerate(citations, 1):
                print(f"   {i}. {cite['filename']} (Score: {cite['score']})")
    else:
        print(f"❌ STATUS: {response.status_code}")
        print(f"ERROR: {response.text}")
    
    print_separator()

if __name__ == "__main__":
    print("\n" + "🎯 " + "="*76 + " 🎯")
    print("   E2E CHAT DEMONSTRATION - Policy RAG Application")
    print("🎯 " + "="*76 + " 🎯")
    print_separator()
    
    # Test 1: Leave Policy
    test_chat("tell me about leave policy")
    
    # Test 2: Leave Policy (uppercase)
    test_chat("TELL ME ABOUT LEAVE POLICY")
    
    # Test 3: Specific question - annual leave
    test_chat("How many vacation days do I get?")
    
    # Test 4: Sick leave
    test_chat("What is the sick leave policy?")
    
    # Test 5: Remote work
    test_chat("Can I work from home?")
    
    # Test 6: Data privacy
    test_chat("What are the data retention requirements?")
    
    # Test 7: NDA
    test_chat("Tell me about the NDA")
    
    # Test 8: Vague query
    test_chat("Tell me about policy")
    
    print("\n✅ E2E DEMONSTRATION COMPLETE!")
    print("All responses above are actual API responses from the running server.\n")
