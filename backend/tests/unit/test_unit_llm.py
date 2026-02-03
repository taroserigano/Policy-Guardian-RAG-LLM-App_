"""
Unit Tests for LLM Provider Functions
Tests individual functions in isolation with mocking
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path setup
try:
    import simple_server
except ImportError:
    # Try alternative import
    from backend import simple_server


class TestOllamaFunction(unittest.TestCase):
    """Unit tests for call_ollama function"""
    
    @patch('simple_server.requests.post')
    def test_ollama_success(self, mock_post):
        """Test successful Ollama API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Test response from Ollama"}
        }
        mock_post.return_value = mock_response
        
        # Call function
        messages = [{"role": "user", "content": "test"}]
        result = simple_server.call_ollama("llama3.1:8b", messages, "context")
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, "Test response from Ollama")
        mock_post.assert_called_once()
        
    @patch('simple_server.requests.post')
    def test_ollama_failure_returns_none(self, mock_post):
        """Test Ollama returns None on error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "test"}]
        result = simple_server.call_ollama("llama3.1:8b", messages, "context")
        
        self.assertIsNone(result)
        
    @patch('simple_server.requests.post')
    def test_ollama_exception_handling(self, mock_post):
        """Test Ollama handles exceptions gracefully"""
        mock_post.side_effect = Exception("Connection error")
        
        messages = [{"role": "user", "content": "test"}]
        result = simple_server.call_ollama("llama3.1:8b", messages, "context")
        
        self.assertIsNone(result)


class TestOpenAIFunction(unittest.TestCase):
    """Unit tests for call_openai function"""
    
    @patch('simple_server.requests.post')
    def test_openai_success(self, mock_post):
        """Test successful OpenAI API call"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response from OpenAI"}}]
        }
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "test"}]
        result = simple_server.call_openai("gpt-4o-mini", messages, "test-key")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, "Test response from OpenAI")
        
    @patch('simple_server.requests.post')
    def test_openai_with_conversation_history(self, mock_post):
        """Test OpenAI handles conversation history"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_post.return_value = mock_response
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"}
        ]
        result = simple_server.call_openai("gpt-4o-mini", messages, "test-key")
        
        self.assertIsNotNone(result)
        call_args = mock_post.call_args
        sent_messages = call_args[1]['json']['messages']
        self.assertEqual(len(sent_messages), 3)


class TestAnthropicFunction(unittest.TestCase):
    """Unit tests for call_anthropic function"""
    
    @patch('simple_server.requests.post')
    def test_anthropic_success(self, mock_post):
        """Test successful Anthropic API call"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Test response from Claude"}]
        }
        mock_post.return_value = mock_response
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "test"}
        ]
        result = simple_server.call_anthropic("claude-3-sonnet-20240229", messages, "test-key")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, "Test response from Claude")
        
    @patch('simple_server.requests.post')
    def test_anthropic_system_message_extraction(self, mock_post):
        """Test Anthropic extracts system message correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}]
        }
        mock_post.return_value = mock_response
        
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"}
        ]
        simple_server.call_anthropic("claude-3-sonnet-20240229", messages, "test-key")
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['system'], "System prompt")
        self.assertEqual(len(payload['messages']), 1)
        self.assertEqual(payload['messages'][0]['role'], "user")
        
    @patch('simple_server.requests.post')
    def test_anthropic_404_model_not_found(self, mock_post):
        """Test Anthropic handles 404 model not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = '{"type":"error","error":{"type":"not_found_error","message":"model not found"}}'
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "test"}]
        result = simple_server.call_anthropic("invalid-model", messages, "test-key")
        
        self.assertIsNone(result)


class TestConversationMemory(unittest.TestCase):
    """Unit tests for conversation memory management"""
    
    def test_conversation_history_stores_messages(self):
        """Test that conversation history is stored"""
        # This tests the data structure used
        conversation_history = {}
        user_id = "test_user"
        
        # Add messages
        conversation_history[user_id] = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "Hi", "timestamp": "2024-01-01T10:00:01"}
        ]
        
        self.assertEqual(len(conversation_history[user_id]), 2)
        self.assertEqual(conversation_history[user_id][0]["content"], "Hello")
        
    def test_conversation_history_limits_messages(self):
        """Test that conversation history is limited"""
        history = []
        
        # Add 25 messages (should keep only last 20)
        for i in range(25):
            history.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
                "timestamp": f"2024-01-01T10:{i:02d}:00"
            })
        
        # Simulate the limit logic (keep last 20)
        if len(history) > 20:
            history = history[-20:]
        
        self.assertEqual(len(history), 20)
        self.assertEqual(history[0]["content"], "Message 5")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
