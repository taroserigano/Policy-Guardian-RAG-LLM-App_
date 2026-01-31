"""
Simple multimodal test - no app imports to avoid server conflicts
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"

print("\n=== MULTIMODAL CHAT TEST ===\n")

# Step 1: Get documents
print("1️⃣  Getting documents...")
time.sleep(2)  # Wait for server to start
docs_resp = requests.get(f"{BASE_URL}/api/docs")
docs = docs_resp.json()
print(f"   Found {len(docs)} documents")

# Find workplace compliance doc
compliance_doc = None
for doc in docs:
    if 'compliance' in doc['filename'].lower() or 'workplace' in doc['filename'].lower():
        compliance_doc = doc
        break

if not compliance_doc:
    print("   ❌ No compliance document found")
    exit(1)

print(f"   ✅ Using: {compliance_doc['filename']}")
print(f"   Doc ID: {compliance_doc['id']}")

# Step 2: Get images
print("\n2️⃣  Getting images...")
images_resp = requests.get(f"{BASE_URL}/api/images/")
images = images_resp.json()
print(f"   Found {len(images)} images")

if not images:
    print("   ❌ No images found")
    exit(1)

test_image = images[0]
print(f"   ✅ Using: {test_image['filename']}")
print(f"   Image ID: {test_image['id']}")
print(f"   Description preview: {test_image.get('description', 'No description')[:100]}...")

# Step 3: Make multimodal query
print("\n3️⃣  Making multimodal query...")
question = "Does the person's attire comply with the workplace dress code policy? Be specific about what items match or don't match the requirements."

payload = {
    "user_id": "test-user",
    "provider": "ollama",
    "question": question,
    "doc_ids": [compliance_doc['id']],
    "image_ids": [test_image['id']],
    "top_k": 5
}

print(f"   Question: {question}")
print(f"   Sending request...")

try:
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=payload,
        stream=True,
        timeout=120
    )
    
    if response.status_code != 200:
        print(f"   ❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
    
    print(f"   ✅ Streaming response...\n")
    
    # Collect response
    full_answer = ""
    citations = []
    token_count = 0
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                try:
                    data = json.loads(data_str)
                    if data['type'] == 'token':
                        token = data['data']
                        full_answer += token
                        token_count += 1
                        # Print progress every 50 tokens
                        if token_count % 50 == 0:
                            print(".", end="", flush=True)
                    elif data['type'] == 'citations':
                        citations = data['data']
                except json.JSONDecodeError:
                    pass
    
    print("\n\n" + "="*70)
    print("RESPONSE:")
    print("="*70)
    print(full_answer)
    print("="*70)
    
    # Analyze response quality
    print("\n4️⃣  Analyzing response quality...\n")
    
    checks = {
        "Has response": len(full_answer) > 50,
        "Mentions clothing items": any(word in full_answer.lower() for word in ['shirt', 'pants', 'top', 'blouse', 'skirt', 'tank', 'shorts', 'clothing', 'attire', 'wear']),
        "References policy": any(word in full_answer.lower() for word in ['policy', 'requirement', 'dress code', 'business casual', 'professional']),
        "Provides assessment": any(word in full_answer.lower() for word in ['comply', 'complies', 'compliant', 'not compliant', 'appropriate', 'inappropriate', 'meets', 'does not meet']),
        "Avoids 'not described'": 'not described' not in full_answer.lower() and 'no description' not in full_answer.lower(),
        "Has citations": len(citations) > 0
    }
    
    passed = 0
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if result:
            passed += 1
    
    print(f"\n{'='*70}")
    print(f"SCORE: {passed}/{len(checks)} checks passed ({passed/len(checks)*100:.0f}%)")
    print(f"{'='*70}\n")
    
    if passed == len(checks):
        print("🎉 ALL TESTS PASSED - Multimodal feature is working correctly!")
    elif passed >= len(checks) * 0.7:
        print("⚠️  Most tests passed - minor improvements needed")
    else:
        print("❌ Multiple tests failed - needs fixing")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
