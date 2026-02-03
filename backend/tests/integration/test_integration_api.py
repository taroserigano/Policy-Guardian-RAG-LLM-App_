"""
Integration Tests for API Endpoints
Tests the full API endpoints with real FastAPI test client
"""
import unittest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from simple_server import app
except ImportError:
    from backend.simple_server import app


class TestHealthEndpoint(unittest.TestCase):
    """Integration tests for health endpoint"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns successful response"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        
    def test_health_endpoint_structure(self):
        """Test health endpoint returns correct structure"""
        response = self.client.get("/health")
        data = response.json()
        
        self.assertIn("status", data)
        self.assertIn("version", data)
        self.assertIn("service", data)
        self.assertEqual(data["status"], "healthy")


class TestDocumentsEndpoint(unittest.TestCase):
    """Integration tests for documents endpoint"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_get_documents_returns_200(self):
        """Test GET documents returns success"""
        response = self.client.get("/api/docs")
        self.assertEqual(response.status_code, 200)
        
    def test_get_documents_structure(self):
        """Test documents endpoint returns correct structure"""
        response = self.client.get("/api/docs")
        data = response.json()
        
        self.assertIn("documents", data)
        self.assertIsInstance(data["documents"], list)
        
    def test_documents_have_required_fields(self):
        """Test each document has required fields"""
        response = self.client.get("/api/docs")
        data = response.json()
        
        if len(data["documents"]) > 0:
            doc = data["documents"][0]
            self.assertIn("id", doc)
            self.assertIn("filename", doc)
            self.assertIn("content_type", doc)


class TestChatEndpointStructure(unittest.TestCase):
    """Integration tests for chat endpoint structure"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_chat_endpoint_requires_question(self):
        """Test chat endpoint requires question field"""
        response = self.client.post("/api/chat", json={
            "user_id": "test"
        })
        self.assertEqual(response.status_code, 422)  # Validation error
        
    def test_chat_endpoint_requires_user_id(self):
        """Test chat endpoint requires user_id field"""
        response = self.client.post("/api/chat", json={
            "question": "test"
        })
        self.assertEqual(response.status_code, 422)  # Validation error
        
    def test_chat_endpoint_accepts_valid_request(self):
        """Test chat endpoint accepts valid request"""
        response = self.client.post("/api/chat", json={
            "question": "What is the leave policy?",
            "user_id": "test_user"
        })
        self.assertEqual(response.status_code, 200)


class TestChatEndpointWithOllama(unittest.TestCase):
    """Integration tests for chat endpoint with Ollama provider"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    @patch('simple_server.call_ollama')
    def test_chat_with_ollama_provider(self, mock_ollama):
        """Test chat with Ollama provider"""
        mock_ollama.return_value = "Mocked Ollama response"
        
        response = self.client.post("/api/chat", json={
            "question": "Test question",
            "user_id": "test_user",
            "provider": "ollama"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("answer", data)
        self.assertIn("citations", data)
        self.assertIn("model", data)
        self.assertEqual(data["model"]["provider"], "ollama")
        
    @patch('simple_server.call_ollama')
    def test_chat_with_custom_ollama_model(self, mock_ollama):
        """Test chat with custom Ollama model"""
        mock_ollama.return_value = "Response"
        
        response = self.client.post("/api/chat", json={
            "question": "Test",
            "user_id": "test",
            "provider": "ollama",
            "model": "gemma2:9b"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model"]["name"], "gemma2:9b")
        
        # Verify the mock was called with the custom model
        mock_ollama.assert_called_once()
        call_args = mock_ollama.call_args[0]
        self.assertEqual(call_args[0], "gemma2:9b")


class TestChatEndpointWithOpenAI(unittest.TestCase):
    """Integration tests for chat endpoint with OpenAI provider"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    @patch('simple_server.call_openai')
    @patch('simple_server.os.getenv')
    def test_chat_with_openai_provider(self, mock_getenv, mock_openai):
        """Test chat with OpenAI provider"""
        mock_getenv.return_value = "test-api-key"
        mock_openai.return_value = "Mocked OpenAI response"
        
        response = self.client.post("/api/chat", json={
            "question": "Test question",
            "user_id": "test_user",
            "provider": "openai"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["model"]["provider"], "openai")
        self.assertEqual(data["answer"], "Mocked OpenAI response")
        
    @patch('simple_server.os.getenv')
    def test_chat_with_openai_no_api_key(self, mock_getenv):
        """Test chat with OpenAI when API key is missing"""
        mock_getenv.return_value = ""
        
        response = self.client.post("/api/chat", json={
            "question": "Test question",
            "user_id": "test_user",
            "provider": "openai"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("API key not configured", data["answer"])


class TestChatEndpointWithAnthropic(unittest.TestCase):
    """Integration tests for chat endpoint with Anthropic provider"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    @patch('simple_server.call_anthropic')
    @patch('simple_server.os.getenv')
    def test_chat_with_anthropic_provider(self, mock_getenv, mock_anthropic):
        """Test chat with Anthropic provider"""
        mock_getenv.return_value = "test-api-key"
        mock_anthropic.return_value = "Mocked Claude response"
        
        response = self.client.post("/api/chat", json={
            "question": "Test question",
            "user_id": "test_user",
            "provider": "anthropic"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["model"]["provider"], "anthropic")
        self.assertEqual(data["answer"], "Mocked Claude response")
        
    @patch('simple_server.call_anthropic')
    @patch('simple_server.os.getenv')
    def test_chat_with_anthropic_fallback_on_failure(self, mock_getenv, mock_anthropic):
        """Test chat falls back to demo when Anthropic fails"""
        mock_getenv.return_value = "test-api-key"
        mock_anthropic.return_value = None  # Simulate API failure
        
        response = self.client.post("/api/chat", json={
            "question": "Test question",
            "user_id": "test_user",
            "provider": "anthropic"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("demo mode", data["answer"].lower())


class TestProviderSwitching(unittest.TestCase):
    """Integration tests for switching between providers"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    @patch('simple_server.call_ollama')
    @patch('simple_server.call_openai')
    @patch('simple_server.os.getenv')
    def test_switch_from_ollama_to_openai(self, mock_getenv, mock_openai, mock_ollama):
        """Test switching from Ollama to OpenAI"""
        mock_getenv.return_value = "test-key"
        mock_ollama.return_value = "Ollama response"
        mock_openai.return_value = "OpenAI response"
        
        user_id = "switch_test_user"
        
        # First request with Ollama
        response1 = self.client.post("/api/chat", json={
            "question": "First question",
            "user_id": user_id,
            "provider": "ollama"
        })
        self.assertEqual(response1.json()["model"]["provider"], "ollama")
        
        # Second request with OpenAI
        response2 = self.client.post("/api/chat", json={
            "question": "Second question",
            "user_id": user_id,
            "provider": "openai"
        })
        self.assertEqual(response2.json()["model"]["provider"], "openai")


if __name__ == "__main__":
    unittest.main(verbosity=2)
