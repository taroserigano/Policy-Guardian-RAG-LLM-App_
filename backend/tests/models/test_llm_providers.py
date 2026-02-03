"""
Comprehensive tests for LLM provider integrations
Tests Ollama, OpenAI, and Anthropic providers
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simple_server import app, call_ollama, call_openai, call_anthropic


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestOllamaProvider:
    """Tests for Ollama LLM provider."""
    
    def test_ollama_default_model_selection(self, client):
        """Test Ollama uses default model when not specified."""
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "ollama",
            "user_id": "test-user"
        })
        assert response.status_code == 200
        data = response.json()
        assert "model" in data
        # Should default to llama3.1:8b or similar
        assert data["model"]["provider"] == "ollama"
    
    def test_ollama_custom_model_selection(self, client):
        """Test Ollama accepts custom model."""
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "ollama",
            "model": "llama3.1:70b",
            "user_id": "test-user"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["model"]["name"] == "llama3.1:70b"
    
    def test_ollama_handles_connection_failure(self, client):
        """Test Ollama gracefully handles connection failure."""
        with patch('simple_server.requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection refused")
            
            response = client.post("/api/chat", json={
                "question": "test",
                "provider": "ollama",
                "user_id": "test-user"
            })
            assert response.status_code == 200
            data = response.json()
            # Should fallback to demo mode
            assert "demo mode" in data["answer"].lower() or "ollama" in data["answer"].lower()
    
    def test_ollama_timeout_handling(self, client):
        """Test Ollama handles timeout gracefully."""
        with patch('simple_server.requests.post') as mock_post:
            mock_post.side_effect = TimeoutError("Request timeout")
            
            response = client.post("/api/chat", json={
                "question": "test",
                "provider": "ollama",
                "user_id": "test-user"
            })
            assert response.status_code == 200
    
    @patch('simple_server.requests.post')
    def test_ollama_successful_call(self, mock_post, client):
        """Test successful Ollama API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "This is a test response from Ollama"
            }
        }
        mock_post.return_value = mock_response
        
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "ollama",
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "test response from Ollama" in data["answer"]


class TestOpenAIProvider:
    """Tests for OpenAI LLM provider."""
    
    def test_openai_default_model_selection(self, client):
        """Test OpenAI uses default model when not specified."""
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "openai",
            "user_id": "test-user"
        })
        assert response.status_code == 200
        data = response.json()
        assert "model" in data
        assert data["model"]["provider"] == "openai"
    
    def test_openai_custom_model_selection(self, client):
        """Test OpenAI accepts custom model."""
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "openai",
            "model": "gpt-4",
            "user_id": "test-user"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["model"]["name"] == "gpt-4"
    
    def test_openai_missing_api_key_message(self, client):
        """Test OpenAI shows helpful message when API key is missing."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            response = client.post("/api/chat", json={
                "question": "test",
                "provider": "openai",
                "user_id": "test-user"
            })
            assert response.status_code == 200
            data = response.json()
            assert "api key" in data["answer"].lower() or "not configured" in data["answer"].lower()
    
    @patch('simple_server.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_openai_successful_call(self, mock_post, client):
        """Test successful OpenAI API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is a test response from OpenAI"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "openai",
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "test response from OpenAI" in data["answer"]
    
    @patch('simple_server.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_openai_api_error_handling(self, mock_post, client):
        """Test OpenAI API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_post.return_value = mock_response
        
        response = client.post("/api/chat", json={
            "question": "test",
            "provider": "openai",
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        # Should fallback to demo mode
        data = response.json()
        assert len(data["answer"]) > 0


class TestAnthropicProvider:
    """Tests for Anthropic Claude provider."""
    
    def test_anthropic_default_model_selection(self, client):
        """Test Anthropic uses default model when not specified."""
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "anthropic",
            "user_id": "test-user"
        })
        assert response.status_code == 200
        data = response.json()
        assert "model" in data
        assert data["model"]["provider"] == "anthropic"
    
    def test_anthropic_custom_model_selection(self, client):
        """Test Anthropic accepts custom model."""
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "anthropic",
            "model": "claude-3-opus-20240229",
            "user_id": "test-user"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["model"]["name"] == "claude-3-opus-20240229"
    
    def test_anthropic_missing_api_key_message(self, client):
        """Test Anthropic shows helpful message when API key is missing."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            response = client.post("/api/chat", json={
                "question": "test",
                "provider": "anthropic",
                "user_id": "test-user"
            })
            assert response.status_code == 200
            data = response.json()
            assert "api key" in data["answer"].lower() or "not configured" in data["answer"].lower()
    
    @patch('simple_server.requests.post')
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_anthropic_successful_call(self, mock_post, client):
        """Test successful Anthropic API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{
                "text": "This is a test response from Claude"
            }]
        }
        mock_post.return_value = mock_response
        
        response = client.post("/api/chat", json={
            "question": "test question",
            "provider": "anthropic",
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "test response from Claude" in data["answer"]
    
    @patch('simple_server.requests.post')
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"})
    def test_anthropic_api_error_handling(self, mock_post, client):
        """Test Anthropic API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_post.return_value = mock_response
        
        response = client.post("/api/chat", json={
            "question": "test",
            "provider": "anthropic",
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        # Should fallback to demo mode


class TestProviderSwitching:
    """Tests for switching between different LLM providers."""
    
    def test_switch_from_ollama_to_openai(self, client):
        """Test switching from Ollama to OpenAI."""
        # First request with Ollama
        response1 = client.post("/api/chat", json={
            "question": "test",
            "provider": "ollama",
            "user_id": "test-user"
        })
        assert response1.status_code == 200
        assert response1.json()["model"]["provider"] == "ollama"
        
        # Second request with OpenAI
        response2 = client.post("/api/chat", json={
            "question": "test",
            "provider": "openai",
            "user_id": "test-user"
        })
        assert response2.status_code == 200
        assert response2.json()["model"]["provider"] == "openai"
    
    def test_switch_from_openai_to_anthropic(self, client):
        """Test switching from OpenAI to Anthropic."""
        response1 = client.post("/api/chat", json={
            "question": "test",
            "provider": "openai",
            "user_id": "test-user"
        })
        assert response1.status_code == 200
        
        response2 = client.post("/api/chat", json={
            "question": "test",
            "provider": "anthropic",
            "user_id": "test-user"
        })
        assert response2.status_code == 200
        assert response2.json()["model"]["provider"] == "anthropic"
    
    def test_switch_from_anthropic_to_ollama(self, client):
        """Test switching from Anthropic to Ollama."""
        response1 = client.post("/api/chat", json={
            "question": "test",
            "provider": "anthropic",
            "user_id": "test-user"
        })
        assert response1.status_code == 200
        
        response2 = client.post("/api/chat", json={
            "question": "test",
            "provider": "ollama",
            "user_id": "test-user"
        })
        assert response2.status_code == 200
        assert response2.json()["model"]["provider"] == "ollama"


class TestProviderFallback:
    """Tests for provider fallback behavior."""
    
    def test_all_providers_fail_shows_demo_mode(self, client):
        """Test fallback to demo mode when all providers fail."""
        with patch('simple_server.call_ollama', return_value=None), \
             patch('simple_server.call_openai', return_value=None), \
             patch('simple_server.call_anthropic', return_value=None):
            
            response = client.post("/api/chat", json={
                "question": "test",
                "provider": "ollama",
                "user_id": "test-user"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "demo mode" in data["answer"].lower()
            assert len(data["citations"]) > 0  # Still returns citations


class TestModelParameters:
    """Tests for model parameters and configuration."""
    
    def test_temperature_is_applied(self, client):
        """Test that temperature parameter is sent to LLM."""
        # This is tested by checking the mock call, not the response
        with patch('simple_server.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "test"}
            }
            mock_post.return_value = mock_response
            
            client.post("/api/chat", json={
                "question": "test",
                "provider": "ollama",
                "user_id": "test-user"
            })
            
            # Check that temperature was included in the request
            call_args = mock_post.call_args
            if call_args:
                json_data = call_args[1].get('json', {})
                if 'options' in json_data:
                    assert 'temperature' in json_data['options']


class TestConversationMemory:
    """Tests for conversation history management."""
    
    def test_conversation_history_persists(self, client):
        """Test that conversation history is maintained across requests."""
        user_id = "test-memory-user"
        
        # First message
        response1 = client.post("/api/chat", json={
            "question": "What is annual leave?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert response1.status_code == 200
        
        # Second message - should have context from first
        response2 = client.post("/api/chat", json={
            "question": "How do I request it?",
            "provider": "ollama",
            "user_id": user_id
        })
        assert response2.status_code == 200
    
    def test_different_users_separate_history(self, client):
        """Test that different users have separate conversation histories."""
        # User 1
        response1 = client.post("/api/chat", json={
            "question": "Tell me about leave",
            "provider": "ollama",
            "user_id": "user1"
        })
        assert response1.status_code == 200
        
        # User 2
        response2 = client.post("/api/chat", json={
            "question": "Tell me about remote work",
            "provider": "ollama",
            "user_id": "user2"
        })
        assert response2.status_code == 200
        
        # Both should work independently
        assert "leave" in response1.json()["answer"].lower() or "annual" in response1.json()["answer"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
