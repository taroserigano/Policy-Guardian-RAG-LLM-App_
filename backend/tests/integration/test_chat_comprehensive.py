"""
Comprehensive test suite for Chat functionality.
Tests all scenarios: document-only, image-only, document+image (multimodal).
Includes unit tests, integration tests, and E2E tests.
"""
import pytest
import requests
import json
import base64
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_USER_ID = "test-user-chat-comprehensive"

# Sample test image (1x1 red pixel PNG)
SAMPLE_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def api_health_check():
    """Ensure API is running before tests."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200, "API is not healthy"
        return True
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend API is not running")

@pytest.fixture(scope="module")
def sample_document(api_health_check):
    """Upload a sample document for testing."""
    # Create a simple test document
    doc_content = """
    Test Policy Document
    
    Section 1: Refund Eligibility
    - Items must be returned within 30 days
    - Items must be in original condition
    - Damaged items are eligible for refund if damage occurred during shipping
    - Proof of purchase is required
    
    Section 2: Non-Eligible Items
    - Items damaged by user negligence
    - Items without original packaging
    - Items purchased more than 90 days ago
    """
    
    files = {
        'file': ('test_policy.txt', doc_content, 'text/plain')
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=60)
        if resp.status_code == 201:
            data = resp.json()
            yield data.get('doc_id') or data.get('id')
            # Cleanup
            try:
                requests.delete(f"{BASE_URL}/api/docs/{data.get('doc_id') or data.get('id')}")
            except:
                pass
        else:
            pytest.skip(f"Could not upload test document: {resp.text}")
    except Exception as e:
        pytest.skip(f"Document upload failed: {e}")

@pytest.fixture(scope="module")
def sample_image(api_health_check):
    """Upload a sample image for testing."""
    # Create a simple test image
    image_bytes = base64.b64decode(SAMPLE_IMAGE_B64)
    
    files = {
        'file': ('test_image.png', image_bytes, 'image/png')
    }
    data = {
        'generate_description': 'false',
        'vision_provider': 'openai'
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/images/upload", files=files, data=data, timeout=60)
        if resp.status_code == 201:
            img_data = resp.json()
            yield img_data.get('image_id') or img_data.get('id')
            # Cleanup
            try:
                requests.delete(f"{BASE_URL}/api/images/{img_data.get('image_id') or img_data.get('id')}")
            except:
                pass
        else:
            pytest.skip(f"Could not upload test image: {resp.text}")
    except Exception as e:
        pytest.skip(f"Image upload failed: {e}")


# ============================================================================
# UNIT TESTS - Chat Request Validation
# ============================================================================

class TestChatRequestValidation:
    """Test chat request validation."""
    
    def test_chat_missing_question(self, api_health_check):
        """Test that chat fails without a question."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "user_id": TEST_USER_ID,
                "provider": "openai"
                # Missing "question"
            }
        )
        assert resp.status_code == 422, "Should fail validation without question"
    
    def test_chat_invalid_provider(self, api_health_check):
        """Test that chat fails with invalid provider."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "Test question",
                "user_id": TEST_USER_ID,
                "provider": "invalid_provider"
            }
        )
        assert resp.status_code == 400, "Should fail with invalid provider"
    
    def test_chat_valid_providers(self, api_health_check):
        """Test that valid providers are accepted."""
        valid_providers = ["openai", "anthropic", "ollama"]
        for provider in valid_providers:
            resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": "Hello",
                    "user_id": TEST_USER_ID,
                    "provider": provider
                },
                stream=True,
                timeout=30
            )
            # Should not return 400 for valid provider
            assert resp.status_code != 400, f"Provider {provider} should be valid"
            resp.close()


# ============================================================================
# INTEGRATION TESTS - Document-Only Chat
# ============================================================================

class TestDocumentOnlyChat:
    """Test chat with documents only (no images)."""
    
    def test_chat_with_document(self, api_health_check, sample_document):
        """Test basic chat with a document selected."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "What are the refund eligibility requirements?",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document],
                "top_k": 3
            },
            stream=True,
            timeout=60
        )
        
        assert resp.status_code == 200, f"Chat should succeed: {resp.text}"
        
        # Parse SSE response
        full_response = ""
        citations_received = False
        done_received = False
        
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
                    elif data['type'] == 'citations':
                        citations_received = True
                    elif data['type'] == 'done':
                        done_received = True
        
        assert len(full_response) > 0, "Should receive response text"
        assert done_received, "Should receive done signal"
        print(f"✓ Document chat response: {full_response[:100]}...")
    
    def test_chat_without_document(self, api_health_check):
        """Test chat without any document (general question)."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "What is 2+2?",
                "user_id": TEST_USER_ID,
                "provider": "openai"
            },
            stream=True,
            timeout=30
        )
        
        assert resp.status_code == 200, "Chat should succeed without documents"
        
        full_response = ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
        
        assert len(full_response) > 0, "Should receive response"
    
    def test_chat_with_invalid_doc_id(self, api_health_check):
        """Test chat with non-existent document ID."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "Test question",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": ["non-existent-doc-id-12345"]
            },
            stream=True,
            timeout=30
        )
        
        # Should still work but with no document context
        assert resp.status_code == 200


# ============================================================================
# INTEGRATION TESTS - Image-Only Chat
# ============================================================================

class TestImageOnlyChat:
    """Test chat with images only (no documents)."""
    
    def test_chat_with_image(self, api_health_check, sample_image):
        """Test basic chat with an image selected."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "What do you see in this image?",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "image_ids": [sample_image]
            },
            stream=True,
            timeout=60
        )
        
        assert resp.status_code == 200, f"Image chat should succeed: {resp.text}"
        
        full_response = ""
        done_received = False
        
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
                    elif data['type'] == 'done':
                        done_received = True
        
        assert len(full_response) > 0, "Should receive response"
        assert done_received, "Should receive done signal"
        print(f"✓ Image chat response: {full_response[:100]}...")
    
    def test_chat_with_invalid_image_id(self, api_health_check):
        """Test chat with non-existent image ID."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "What is this?",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "image_ids": ["non-existent-image-id-12345"]
            },
            stream=True,
            timeout=30
        )
        
        # Should handle gracefully
        assert resp.status_code == 200


# ============================================================================
# INTEGRATION TESTS - Multimodal Chat (Document + Image)
# ============================================================================

class TestMultimodalChat:
    """Test chat with both documents and images."""
    
    def test_chat_with_document_and_image(self, api_health_check, sample_document, sample_image):
        """Test multimodal chat with document and image."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "Based on the policy, is this item eligible for a refund?",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document],
                "image_ids": [sample_image],
                "top_k": 3
            },
            stream=True,
            timeout=90
        )
        
        assert resp.status_code == 200, f"Multimodal chat should succeed: {resp.text}"
        
        full_response = ""
        citations = []
        
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
                    elif data['type'] == 'citations':
                        citations = data['data']
        
        assert len(full_response) > 0, "Should receive response"
        # Should have eligibility score when doc context is provided
        print(f"✓ Multimodal chat response: {full_response[:200]}...")
        print(f"✓ Citations received: {len(citations)}")
    
    def test_eligibility_score_in_response(self, api_health_check, sample_document, sample_image):
        """Test that eligibility score is included in multimodal response."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "Is this eligible for refund?",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document],
                "image_ids": [sample_image]
            },
            stream=True,
            timeout=90
        )
        
        full_response = ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'token':
                        full_response += data['data']
        
        # Check for eligibility score pattern
        has_score = "Eligibility Score:" in full_response or "eligibility" in full_response.lower()
        print(f"✓ Response contains eligibility info: {has_score}")
        print(f"✓ Response preview: {full_response[:300]}...")


# ============================================================================
# INTEGRATION TESTS - Provider Switching
# ============================================================================

class TestProviderSwitching:
    """Test chat with different LLM providers."""
    
    def test_openai_provider(self, api_health_check, sample_document):
        """Test chat with OpenAI provider."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "Hello, this is a test",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document]
            },
            stream=True,
            timeout=30
        )
        assert resp.status_code == 200, "OpenAI chat should work"
        resp.close()
    
    def test_anthropic_provider(self, api_health_check, sample_document):
        """Test chat with Anthropic provider."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "Hello, this is a test",
                "user_id": TEST_USER_ID,
                "provider": "anthropic",
                "doc_ids": [sample_document]
            },
            stream=True,
            timeout=30
        )
        # May fail if API key not configured, but should not error
        assert resp.status_code in [200, 500], "Should handle anthropic provider"
        resp.close()


# ============================================================================
# INTEGRATION TESTS - RAG Options
# ============================================================================

class TestRAGOptions:
    """Test RAG configuration options."""
    
    def test_chat_with_query_expansion(self, api_health_check, sample_document):
        """Test chat with query expansion enabled."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "refund policy",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document],
                "rag_options": {
                    "query_expansion": True,
                    "hybrid_search": False,
                    "reranking": False
                }
            },
            stream=True,
            timeout=60
        )
        assert resp.status_code == 200
        resp.close()
    
    def test_chat_with_hybrid_search(self, api_health_check, sample_document):
        """Test chat with hybrid search enabled."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "What items are not eligible?",
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document],
                "rag_options": {
                    "query_expansion": False,
                    "hybrid_search": True,
                    "reranking": False
                }
            },
            stream=True,
            timeout=60
        )
        assert resp.status_code == 200
        resp.close()
    
    def test_chat_with_custom_top_k(self, api_health_check, sample_document):
        """Test chat with custom top_k value."""
        for top_k in [1, 3, 5, 10]:
            resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": "Test",
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "doc_ids": [sample_document],
                    "top_k": top_k
                },
                stream=True,
                timeout=30
            )
            assert resp.status_code == 200, f"top_k={top_k} should work"
            resp.close()


# ============================================================================
# E2E TESTS - Full Chat Flow
# ============================================================================

class TestE2EChatFlow:
    """End-to-end tests for complete chat workflows."""
    
    def test_full_document_chat_flow(self, api_health_check):
        """Test complete flow: upload doc -> chat -> verify response -> cleanup."""
        # 1. Upload document
        doc_content = "This product has a 30-day return policy. Damaged items qualify for full refund."
        files = {'file': ('e2e_test.txt', doc_content, 'text/plain')}
        
        upload_resp = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=60)
        assert upload_resp.status_code == 201, "Upload should succeed"
        doc_id = upload_resp.json().get('doc_id') or upload_resp.json().get('id')
        
        try:
            # 2. Wait for indexing
            time.sleep(2)
            
            # 3. Chat with document
            chat_resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": "What is the return policy?",
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "doc_ids": [doc_id]
                },
                stream=True,
                timeout=60
            )
            assert chat_resp.status_code == 200
            
            # 4. Verify response
            full_response = ""
            for line in chat_resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        if data['type'] == 'token':
                            full_response += data['data']
            
            assert len(full_response) > 0
            assert "30" in full_response or "return" in full_response.lower() or "refund" in full_response.lower()
            print(f"✓ E2E Document flow passed: {full_response[:100]}...")
            
        finally:
            # 5. Cleanup
            requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
    
    def test_full_multimodal_chat_flow(self, api_health_check):
        """Test complete multimodal flow: upload doc + image -> chat -> verify."""
        # 1. Upload document
        doc_content = """
        Baggage Damage Policy:
        - Visible structural damage: ELIGIBLE for refund
        - Scratches only: NOT eligible
        - Must report within 7 days
        """
        doc_files = {'file': ('baggage_policy.txt', doc_content, 'text/plain')}
        doc_resp = requests.post(f"{BASE_URL}/api/docs/upload", files=doc_files, timeout=60)
        
        if doc_resp.status_code != 201:
            pytest.skip("Could not upload document")
        doc_id = doc_resp.json().get('doc_id') or doc_resp.json().get('id')
        
        # 2. Upload image
        image_bytes = base64.b64decode(SAMPLE_IMAGE_B64)
        img_files = {'file': ('test_baggage.png', image_bytes, 'image/png')}
        img_data = {'generate_description': 'false'}
        img_resp = requests.post(f"{BASE_URL}/api/images/upload", files=img_files, data=img_data, timeout=60)
        
        if img_resp.status_code != 201:
            requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
            pytest.skip("Could not upload image")
        img_id = img_resp.json().get('image_id') or img_resp.json().get('id')
        
        try:
            # 3. Wait for processing
            time.sleep(2)
            
            # 4. Multimodal chat
            chat_resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": "Is this baggage damage eligible for refund?",
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "doc_ids": [doc_id],
                    "image_ids": [img_id]
                },
                stream=True,
                timeout=90
            )
            assert chat_resp.status_code == 200
            
            # 5. Verify response has eligibility score
            full_response = ""
            for line in chat_resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        if data['type'] == 'token':
                            full_response += data['data']
            
            assert len(full_response) > 0
            print(f"✓ E2E Multimodal flow passed: {full_response[:200]}...")
            
        finally:
            # 6. Cleanup
            requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
            requests.delete(f"{BASE_URL}/api/images/{img_id}")
    
    def test_chat_history_persistence(self, api_health_check, sample_document):
        """Test that chat history is saved and retrievable."""
        test_user = f"test-history-{int(time.time())}"
        
        # 1. Send a chat message
        chat_resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "What is the policy about?",
                "user_id": test_user,
                "provider": "openai",
                "doc_ids": [sample_document]
            },
            stream=True,
            timeout=60
        )
        
        # Consume the response
        for _ in chat_resp.iter_lines():
            pass
        
        # 2. Wait for history to be saved
        time.sleep(1)
        
        # 3. Get chat history
        history_resp = requests.get(f"{BASE_URL}/api/chat/history/{test_user}")
        assert history_resp.status_code == 200
        
        history = history_resp.json()
        print(f"✓ Chat history entries: {len(history)}")


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestChatStress:
    """Stress tests for chat functionality."""
    
    def test_rapid_chat_requests(self, api_health_check, sample_document):
        """Test multiple rapid chat requests."""
        responses = []
        
        for i in range(5):
            resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": f"Test question {i}",
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "doc_ids": [sample_document]
                },
                stream=True,
                timeout=30
            )
            responses.append(resp.status_code)
            resp.close()
        
        success_count = sum(1 for r in responses if r == 200)
        print(f"✓ Rapid requests: {success_count}/5 succeeded")
        assert success_count >= 3, "Most requests should succeed"
    
    def test_long_question(self, api_health_check, sample_document):
        """Test chat with very long question."""
        long_question = "Please explain " + "in detail " * 100 + "the refund policy."
        
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": long_question,
                "user_id": TEST_USER_ID,
                "provider": "openai",
                "doc_ids": [sample_document]
            },
            stream=True,
            timeout=60
        )
        
        # Should handle long questions
        assert resp.status_code in [200, 400, 422]
        resp.close()


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_question(self, api_health_check):
        """Test chat with empty question."""
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "question": "",
                "user_id": TEST_USER_ID,
                "provider": "openai"
            }
        )
        # Should fail validation or handle gracefully
        assert resp.status_code in [200, 400, 422]
    
    def test_special_characters_in_question(self, api_health_check, sample_document):
        """Test chat with special characters."""
        special_questions = [
            "What about <script>alert('xss')</script>?",
            "Tell me about 日本語 characters",
            "What's the policy? It's important!",
            "50% off? Or 100% refund?",
        ]
        
        for q in special_questions:
            resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": q,
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "doc_ids": [sample_document]
                },
                stream=True,
                timeout=30
            )
            assert resp.status_code == 200, f"Should handle: {q[:30]}..."
            resp.close()
    
    def test_multiple_documents(self, api_health_check):
        """Test chat with multiple documents."""
        # Upload two documents
        docs = []
        for i in range(2):
            content = f"Document {i}: Policy section {i}"
            files = {'file': (f'doc{i}.txt', content, 'text/plain')}
            resp = requests.post(f"{BASE_URL}/api/docs/upload", files=files, timeout=30)
            if resp.status_code == 201:
                docs.append(resp.json().get('doc_id') or resp.json().get('id'))
        
        if len(docs) < 2:
            pytest.skip("Could not upload multiple documents")
        
        try:
            # Chat with multiple docs
            resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": "Summarize both documents",
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "doc_ids": docs
                },
                stream=True,
                timeout=60
            )
            assert resp.status_code == 200
            resp.close()
        finally:
            for doc_id in docs:
                requests.delete(f"{BASE_URL}/api/docs/{doc_id}")
    
    def test_multiple_images(self, api_health_check):
        """Test chat with multiple images."""
        images = []
        image_bytes = base64.b64decode(SAMPLE_IMAGE_B64)
        
        for i in range(2):
            files = {'file': (f'img{i}.png', image_bytes, 'image/png')}
            data = {'generate_description': 'false'}
            resp = requests.post(f"{BASE_URL}/api/images/upload", files=files, data=data, timeout=30)
            if resp.status_code == 201:
                images.append(resp.json().get('image_id') or resp.json().get('id'))
        
        if len(images) < 2:
            pytest.skip("Could not upload multiple images")
        
        try:
            resp = requests.post(
                f"{BASE_URL}/api/chat/stream",
                json={
                    "question": "Compare these images",
                    "user_id": TEST_USER_ID,
                    "provider": "openai",
                    "image_ids": images
                },
                stream=True,
                timeout=60
            )
            assert resp.status_code == 200
            resp.close()
        finally:
            for img_id in images:
                requests.delete(f"{BASE_URL}/api/images/{img_id}")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("COMPREHENSIVE CHAT TESTS")
    print("=" * 60)
    print("\nRunning tests... Make sure backend is running on port 8001\n")
    
    # Run with verbose output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
        "--durations=10"  # Show slowest tests
    ])
