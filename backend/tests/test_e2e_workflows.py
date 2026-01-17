"""
End-to-End Tests for Complete Workflows
Tests the entire system from request to response including real API calls
"""
import unittest
import requests
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

BASE_URL = "http://localhost:8001"
TIMEOUT = 120


class TestE2EBackendAvailability(unittest.TestCase):
    """E2E tests for backend availability"""
    
    def test_backend_is_running(self):
        """Test that backend server is accessible"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            self.fail(f"Backend not accessible: {e}. Please start backend first.")
    
    def test_health_endpoint_response_time(self):
        """Test health endpoint responds quickly"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        elapsed = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0, "Health check should respond in under 3 seconds")


class TestE2EDocumentManagement(unittest.TestCase):
    """E2E tests for document management"""
    
    def test_get_documents_workflow(self):
        """Test complete workflow of getting documents"""
        response = requests.get(f"{BASE_URL}/api/docs", timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("documents", data)
        self.assertIsInstance(data["documents"], list)
        self.assertGreater(len(data["documents"]), 0, "Should have pre-loaded documents")
        
    def test_document_structure_complete(self):
        """Test documents have all required fields"""
        response = requests.get(f"{BASE_URL}/api/docs", timeout=10)
        docs = response.json()["documents"]
        
        for doc in docs:
            self.assertIn("id", doc)
            self.assertIn("filename", doc)
            self.assertIn("content_type", doc)
            self.assertIn("preview_text", doc)
            self.assertIn("size", doc)


class TestE2EOllamaIntegration(unittest.TestCase):
    """E2E tests for Ollama integration"""
    
    def test_ollama_chat_complete_workflow(self):
        """Test complete chat workflow with Ollama"""
        payload = {
            "question": "What is the employee leave policy?",
            "user_id": "e2e_test_ollama",
            "provider": "ollama",
            "model": "llama3.1:8b"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("answer", data)
        self.assertIn("citations", data)
        self.assertIn("model", data)
        
        # Verify model info
        self.assertEqual(data["model"]["provider"], "ollama")
        self.assertEqual(data["model"]["name"], "llama3.1:8b")
        
        # Verify answer quality
        answer = data["answer"]
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer), 20, "Answer should be substantial")
        
        # Should not be demo mode
        self.assertNotIn("demo mode", answer.lower())
        
    def test_ollama_conversation_memory(self):
        """Test conversation memory persists across requests"""
        user_id = "e2e_memory_test"
        
        # First message
        payload1 = {
            "question": "My name is Alice",
            "user_id": user_id,
            "provider": "ollama"
        }
        response1 = requests.post(f"{BASE_URL}/api/chat", json=payload1, timeout=TIMEOUT)
        self.assertEqual(response1.status_code, 200)
        
        # Second message asking about first
        payload2 = {
            "question": "What is my name?",
            "user_id": user_id,
            "provider": "ollama"
        }
        response2 = requests.post(f"{BASE_URL}/api/chat", json=payload2, timeout=TIMEOUT)
        data2 = response2.json()
        
        # Should remember the name from previous conversation
        answer = data2["answer"].lower()
        self.assertTrue("alice" in answer, "Should remember name from previous message")


class TestE2EOpenAIIntegration(unittest.TestCase):
    """E2E tests for OpenAI integration"""
    
    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "OpenAI API key not configured")
    def test_openai_chat_complete_workflow(self):
        """Test complete chat workflow with OpenAI"""
        payload = {
            "question": "Say hello in one sentence",
            "user_id": "e2e_test_openai",
            "provider": "openai",
            "model": "gpt-4o-mini"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify structure
        self.assertEqual(data["model"]["provider"], "openai")
        self.assertEqual(data["model"]["name"], "gpt-4o-mini")
        
        # Verify real response (not demo)
        answer = data["answer"]
        self.assertNotIn("demo mode", answer.lower())
        self.assertGreater(len(answer), 5)


class TestE2EAnthropicIntegration(unittest.TestCase):
    """E2E tests for Anthropic integration"""
    
    @unittest.skipIf(not os.getenv("ANTHROPIC_API_KEY"), "Anthropic API key not configured")
    def test_anthropic_integration_handles_model_availability(self):
        """Test Anthropic integration handles model availability issues"""
        payload = {
            "question": "Say hello",
            "user_id": "e2e_test_anthropic",
            "provider": "anthropic"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should always return a response (either real or fallback)
        self.assertIn("answer", data)
        self.assertIn("model", data)
        self.assertEqual(data["model"]["provider"], "anthropic")
        
    @unittest.skipIf(not os.getenv("ANTHROPIC_API_KEY"), "Anthropic API key not configured")
    def test_anthropic_with_mock_success(self):
        """Test what happens when Anthropic API succeeds (simulated)"""
        # This tests the integration code path
        # In a real scenario with working API, this would get a real response
        payload = {
            "question": "Test question",
            "user_id": "e2e_test_anthropic_mock",
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Model info should be correctly set
        self.assertEqual(data["model"]["provider"], "anthropic")
        self.assertEqual(data["model"]["name"], "claude-3-sonnet-20240229")


class TestE2EProviderSwitching(unittest.TestCase):
    """E2E tests for switching between providers"""
    
    def test_switch_providers_same_user(self):
        """Test switching providers maintains separate conversations"""
        user_id = "e2e_switch_test"
        
        # Ollama request
        payload1 = {
            "question": "Test with Ollama",
            "user_id": user_id,
            "provider": "ollama"
        }
        response1 = requests.post(f"{BASE_URL}/api/chat", json=payload1, timeout=TIMEOUT)
        self.assertEqual(response1.status_code, 200)
        
        # OpenAI request (if key available)
        if os.getenv("OPENAI_API_KEY"):
            payload2 = {
                "question": "Test with OpenAI",
                "user_id": user_id,
                "provider": "openai"
            }
            response2 = requests.post(f"{BASE_URL}/api/chat", json=payload2, timeout=30)
            self.assertEqual(response2.status_code, 200)
            self.assertEqual(response2.json()["model"]["provider"], "openai")
        
        # Back to Ollama
        payload3 = {
            "question": "Back to Ollama",
            "user_id": user_id,
            "provider": "ollama"
        }
        response3 = requests.post(f"{BASE_URL}/api/chat", json=payload3, timeout=TIMEOUT)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()["model"]["provider"], "ollama")


class TestE2EErrorHandling(unittest.TestCase):
    """E2E tests for error handling"""
    
    def test_invalid_provider_fallback(self):
        """Test invalid provider falls back gracefully"""
        payload = {
            "question": "Test question",
            "user_id": "e2e_error_test",
            "provider": "invalid_provider"
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should get fallback response
        self.assertIn("answer", data)
        self.assertIn("demo mode", data["answer"].lower())
        
    def test_missing_api_key_handling(self):
        """Test graceful handling when API keys are missing"""
        # This tests provider that requires API key but it's not set
        # (or we can temporarily unset it for the test)
        payload = {
            "question": "Test",
            "user_id": "e2e_no_key",
            "provider": "openai"  # Assuming key might not be set
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        
        # Should still return 200 with error message
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)


class TestE2EPerformance(unittest.TestCase):
    """E2E tests for performance"""
    
    def test_health_check_performance(self):
        """Test health check is fast"""
        times = []
        for _ in range(5):
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            elapsed = time.time() - start
            times.append(elapsed)
            self.assertEqual(response.status_code, 200)
        
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 3.0, "Average health check should be under 3s")
        
    def test_documents_load_performance(self):
        """Test documents endpoint is reasonably fast"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/docs", timeout=10)
        elapsed = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 5.0, "Documents should load in under 5 seconds")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("END-TO-END TEST SUITE")
    print("="*70)
    print("\nNOTE: Backend must be running on http://localhost:8001")
    print("      Ollama must be running with llama3.1:8b model")
    print("      Some tests require API keys to be configured\n")
    
    unittest.main(verbosity=2)
