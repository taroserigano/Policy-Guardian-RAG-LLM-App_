"""
Debug test - check what's actually being sent from frontend
"""
import requests
import json

BASE_URL = "http://localhost:8001"

print("\n=== FRONTEND SIMULATION TEST ===\n")

# Get resources
docs = requests.get(f"{BASE_URL}/api/docs").json()
images = requests.get(f"{BASE_URL}/api/images/").json()

compliance_doc = next((d for d in docs if 'compliance' in d['filename'].lower()), None)
test_image = images[0] if images else None

if not compliance_doc or not test_image:
    print("Missing resources")
    exit(1)

print(f"Doc: {compliance_doc['filename']} ({compliance_doc['id']})")
print(f"Image: {test_image['filename']} ({test_image['id']})")

# Test with OPENAI provider (what frontend might be using)
providers_to_test = ["ollama", "openai"]

for provider in providers_to_test:
    print(f"\n{'='*70}")
    print(f"Testing with provider: {provider}")
    print(f"{'='*70}")
    
    payload = {
        "user_id": "debug-user",
        "provider": provider,
        "question": "Is this outfit appropriate for the office?",
        "doc_ids": [compliance_doc['id']],
        "image_ids": [test_image['id']],
        "top_k": 5
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
            continue
        
        full_answer = ""
        event_count = {"token": 0, "citations": 0, "other": 0}
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        event_type = data.get('type')
                        if event_type == 'token':
                            full_answer += data['data']
                            event_count['token'] += 1
                        elif event_type == 'citations':
                            event_count['citations'] += 1
                        else:
                            event_count['other'] += 1
                    except:
                        pass
        
        print(f"\nEvents received: {event_count}")
        print(f"Response length: {len(full_answer)} chars")
        
        if len(full_answer) > 0:
            print(f"✅ GOT RESPONSE with {provider}")
            print(f"First 200 chars: {full_answer[:200]}...")
        else:
            print(f"❌ EMPTY RESPONSE with {provider}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*70}")
print("SUMMARY: Check which provider works")
print(f"{'='*70}\n")
