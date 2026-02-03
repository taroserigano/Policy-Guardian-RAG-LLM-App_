"""
Test Pydantic schemas.
"""
import pytest
from pydantic import ValidationError

from app.schemas import (
    ChatRequest,
    ChatResponse,
    CitationResponse,
    ModelInfo,
    DocumentResponse
)


class TestChatRequest:
    """Test ChatRequest schema validation."""
    
    def test_valid_chat_request(self):
        """Test creating valid chat request."""
        request = ChatRequest(
            user_id="user-123",
            provider="ollama",
            question="What is the policy?"
        )
        
        assert request.user_id == "user-123"
        assert request.provider == "ollama"
        assert request.question == "What is the policy?"
        assert request.top_k == 5  # default value
    
    def test_chat_request_with_optional_fields(self):
        """Test chat request with all optional fields."""
        request = ChatRequest(
            user_id="user-456",
            provider="openai",
            model="gpt-4",
            question="Test question",
            doc_ids=["doc-1", "doc-2"],
            top_k=10
        )
        
        assert request.model == "gpt-4"
        assert request.doc_ids == ["doc-1", "doc-2"]
        assert request.top_k == 10
    
    def test_chat_request_missing_required_field(self):
        """Test chat request without required fields."""
        with pytest.raises(ValidationError):
            ChatRequest(
                user_id="user-123",
                # Missing provider
                question="Test"
            )
    
    def test_chat_request_empty_question(self):
        """Test chat request with empty question."""
        with pytest.raises(ValidationError):
            ChatRequest(
                user_id="user-123",
                provider="ollama",
                question=""  # Empty string should fail
            )
    
    def test_chat_request_top_k_validation(self):
        """Test top_k range validation."""
        # Valid range
        request = ChatRequest(
            user_id="user-123",
            provider="ollama",
            question="Test",
            top_k=10
        )
        assert request.top_k == 10
        
        # Test boundary
        request_min = ChatRequest(
            user_id="user-123",
            provider="ollama",
            question="Test",
            top_k=1
        )
        assert request_min.top_k == 1
        
        request_max = ChatRequest(
            user_id="user-123",
            provider="ollama",
            question="Test",
            top_k=20
        )
        assert request_max.top_k == 20


class TestChatResponse:
    """Test ChatResponse schema."""
    
    def test_valid_chat_response(self):
        """Test creating valid chat response."""
        response = ChatResponse(
            answer="The policy states...",
            citations=[
                CitationResponse(
                    doc_id="doc-1",
                    filename="policy.pdf",
                    page_number=5,
                    chunk_index=2,
                    score=0.89
                )
            ],
            model=ModelInfo(provider="ollama", name="llama3.1")
        )
        
        assert response.answer == "The policy states..."
        assert len(response.citations) == 1
        assert response.model.provider == "ollama"
    
    def test_chat_response_no_citations(self):
        """Test chat response without citations."""
        response = ChatResponse(
            answer="No relevant information found.",
            citations=[],
            model=ModelInfo(provider="openai", name="gpt-4")
        )
        
        assert len(response.citations) == 0


class TestCitationResponse:
    """Test CitationResponse schema."""
    
    def test_citation_with_page_number(self):
        """Test citation for PDF with page number."""
        citation = CitationResponse(
            doc_id="doc-1",
            filename="policy.pdf",
            page_number=10,
            chunk_index=5,
            score=0.92
        )
        
        assert citation.page_number == 10
        assert citation.chunk_index == 5
        assert citation.score == 0.92
    
    def test_citation_without_page_number(self):
        """Test citation for TXT without page number."""
        citation = CitationResponse(
            doc_id="doc-2",
            filename="policy.txt",
            chunk_index=3,
            score=0.85
        )
        
        assert citation.page_number is None
        assert citation.chunk_index == 3
