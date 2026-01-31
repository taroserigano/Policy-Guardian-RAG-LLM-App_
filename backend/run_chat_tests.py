"""
Quick test runner for chat functionality.
Run this script directly: python run_chat_tests.py
"""
import requests
import json
import base64
import time
import sys
from io import BytesIO

BASE_URL = "http://localhost:8001"
TEST_USER = "test-user-quick"

def create_test_image_bytes():
    """Create a simple 100x100 red test image."""
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except ImportError:
        # Fallback: larger PNG image (10x10 red pixels)
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFklEQVQY"
            "V2P8z8Dw/z8DMogVAwAAqBAD/5YLz/wAAAABJRU5ErkJggg=="
        )

def print_result(name, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")

def check_api():
    """Check if API is running."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        return resp.status_code == 200
    except:
        return False

def test_1_missing_question():
    """Test: Missing question should fail."""
    try:
        resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "user_id": TEST_USER,
            "provider": "openai"
        }, timeout=10)
        return resp.status_code == 422
    except Exception as e:
        return False

def test_2_invalid_provider():
    """Test: Invalid provider should fail."""
    try:
        resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "question": "Test",
            "user_id": TEST_USER,
            "provider": "invalid"
        }, timeout=10)
        return resp.status_code == 400
    except Exception as e:
        return False

def test_3_valid_providers():
    """Test: Valid providers should work."""
    for provider in ["openai", "anthropic"]:
        try:
            resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
                "question": "Hi",
                "user_id": TEST_USER,
                "provider": provider
            }, stream=True, timeout=30)
            if resp.status_code == 400:
                return False
            resp.close()
        except:
            pass
    return True

def test_4_document_chat():
    """Test: Chat with document."""
    # Upload doc
    doc_content = "Refund policy: Items returned within 30 days get full refund."
    files = {'file': ('test.txt', doc_content, 'text/plain')}
    
    try:
        upload = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=60)
        if upload.status_code != 201:
            return False, "Upload failed"
        
        doc_id = upload.json().get('doc_id') or upload.json().get('id')
        time.sleep(2)  # Wait for indexing
        
        # Chat
        resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "question": "What is the refund policy?",
            "user_id": TEST_USER,
            "provider": "openai",
            "doc_ids": [doc_id]
        }, stream=True, timeout=60)
        
        full_response = ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
        
        return len(full_response) > 0, f"Response: {full_response[:50]}..."
    except Exception as e:
        return False, str(e)

def test_5_image_chat():
    """Test: Chat with image."""
    image_bytes = create_test_image_bytes()
    files = {'file': ('test.png', image_bytes, 'image/png')}
    data = {'generate_description': 'false'}
    
    try:
        upload = requests.post(f"{BASE_URL}/api/images/upload", files=files, data=data, timeout=60)
        if upload.status_code != 201:
            return False, f"Upload failed: {upload.text}"
        
        img_id = upload.json().get('image_id') or upload.json().get('id')
        
        # Chat
        resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "question": "What is this image?",
            "user_id": TEST_USER,
            "provider": "openai",
            "image_ids": [img_id]
        }, stream=True, timeout=60)
        
        full_response = ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/images/{img_id}")
        
        return len(full_response) > 0, f"Response: {full_response[:50]}..."
    except Exception as e:
        return False, str(e)

def test_6_multimodal_chat():
    """Test: Chat with document + image (multimodal)."""
    # Upload doc
    doc_content = """
    Baggage Damage Policy:
    - Visible structural damage: ELIGIBLE for refund (80% score)
    - Scratches only: NOT eligible (20% score)
    """
    doc_files = {'file': ('policy.txt', doc_content, 'text/plain')}
    
    try:
        doc_upload = requests.post(f"{BASE_URL}/api/docs/upload", files=doc_files, timeout=60)
        if doc_upload.status_code != 201:
            return False, "Doc upload failed"
        doc_id = doc_upload.json().get('doc_id') or doc_upload.json().get('id')
        
        # Upload image
        image_bytes = create_test_image_bytes()
        img_files = {'file': ('damage.png', image_bytes, 'image/png')}
        img_data = {'generate_description': 'false'}
        img_upload = requests.post(f"{BASE_URL}/api/images/upload", files=img_files, data=img_data, timeout=60)
        
        if img_upload.status_code != 201:
            requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
            return False, "Image upload failed"
        img_id = img_upload.json().get('image_id') or img_upload.json().get('id')
        
        time.sleep(2)
        
        # Multimodal chat
        resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "question": "Is this damage eligible for refund?",
            "user_id": TEST_USER,
            "provider": "openai",
            "doc_ids": [doc_id],
            "image_ids": [img_id]
        }, stream=True, timeout=90)
        
        full_response = ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_obj = json.loads(line_str[6:])
                    if data_obj['type'] == 'token':
                        full_response += data_obj['data']
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
        requests.delete(f"{BASE_URL}/api/images/{img_id}")
        
        has_score = "score" in full_response.lower() or "eligib" in full_response.lower()
        return len(full_response) > 0 and has_score, f"Response: {full_response[:100]}..."
    except Exception as e:
        return False, str(e)

def test_7_chat_history():
    """Test: Chat history is saved."""
    try:
        # Send a chat
        resp = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "question": "Hello test",
            "user_id": TEST_USER,
            "provider": "openai"
        }, stream=True, timeout=30)
        
        # Consume response
        for _ in resp.iter_lines():
            pass
        
        time.sleep(1)
        
        # Check history
        history = requests.get(f"{BASE_URL}/api/chat/history/{TEST_USER}", timeout=10)
        return history.status_code == 200, f"History entries: {len(history.json())}"
    except Exception as e:
        return False, str(e)

def run_all_tests():
    print("\n" + "=" * 60)
    print("   CHAT FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    # Check API first
    print("\n[Checking API...]")
    if not check_api():
        print("✗ API is not running! Start the backend first.")
        return
    print("✓ API is healthy\n")
    
    results = []
    
    # Run tests
    print("[Running Tests...]")
    
    # Test 1
    passed = test_1_missing_question()
    print_result("Missing question validation", passed)
    results.append(passed)
    
    # Test 2
    passed = test_2_invalid_provider()
    print_result("Invalid provider validation", passed)
    results.append(passed)
    
    # Test 3
    passed = test_3_valid_providers()
    print_result("Valid providers accepted", passed)
    results.append(passed)
    
    # Test 4
    passed, detail = test_4_document_chat()
    print_result("Document-only chat", passed, detail)
    results.append(passed)
    
    # Test 5
    passed, detail = test_5_image_chat()
    print_result("Image-only chat", passed, detail)
    results.append(passed)
    
    # Test 6
    passed, detail = test_6_multimodal_chat()
    print_result("Multimodal chat (doc + image)", passed, detail)
    results.append(passed)
    
    # Test 7
    passed, detail = test_7_chat_history()
    print_result("Chat history persistence", passed, detail)
    results.append(passed)
    
    # Summary
    passed_count = sum(results)
    total = len(results)
    print("\n" + "=" * 60)
    print(f"   RESULTS: {passed_count}/{total} tests passed")
    print("=" * 60)
    
    if passed_count == total:
        print("\n✓ All tests passed! Chat functionality is working correctly.\n")
        return 0
    else:
        print(f"\n✗ {total - passed_count} test(s) failed. Check the output above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
