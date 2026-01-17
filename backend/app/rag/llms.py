"""
LLM provider wrappers for chat completion.
Supports Ollama (local), OpenAI, and Anthropic.
"""
from typing import Optional, Dict, Any
import requests
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class OllamaChat:
    """
    Wrapper for Ollama chat API.
    Uses local Ollama server for chat completions.
    """
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_chat_model
        self.endpoint = f"{self.base_url}/api/chat"
    
    def invoke(self, messages: list) -> str:
        """
        Send chat messages and get completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     e.g., [{"role": "system", "content": "..."}, 
                            {"role": "user", "content": "..."}]
        
        Returns:
            Assistant's response text
        """
        try:
            # Convert LangChain-style messages to Ollama format
            ollama_messages = []
            for msg in messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    # LangChain message object
                    role = msg.type if msg.type != 'ai' else 'assistant'
                    content = msg.content
                elif isinstance(msg, dict):
                    # Already a dict
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                else:
                    continue
                
                ollama_messages.append({"role": role, "content": content})
            
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling Ollama chat: {e}")
            raise


def get_llm(provider: str, model: Optional[str] = None) -> Any:
    """
    Factory function to get appropriate LLM.
    
    Args:
        provider: "ollama", "openai", or "anthropic"
        model: Optional specific model name (uses default if not provided)
    
    Returns:
        LLM instance with invoke() method
    """
    if provider == "ollama":
        return OllamaChat(model=model)
    
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=model or settings.openai_chat_model,
            temperature=0  # Deterministic for legal/compliance use case
        )
    
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=model or settings.anthropic_chat_model,
            temperature=0
        )
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
