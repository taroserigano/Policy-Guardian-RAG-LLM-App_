"""
Unit Tests for Advanced RAG Options
Tests individual components: query_processor, reranker, hybrid search
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Query Processor Unit Tests
# ============================================================================

class TestQueryExpansion:
    """Unit tests for query expansion functionality."""
    
    def test_expand_query_returns_list(self):
        """Test that expand_query returns a list."""
        from app.rag.query_processor import expand_query
        
        with patch('app.rag.query_processor.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "What is the leave policy?\nHow much vacation time do employees get?"
            mock_llm.return_value.invoke.return_value = mock_response
            
            result = expand_query("What is the leave policy?", provider="ollama")
            
            assert isinstance(result, list)
            assert len(result) >= 1
    
    def test_expand_query_includes_original(self):
        """Test that original query is always included."""
        from app.rag.query_processor import expand_query
        
        original_query = "What are the security requirements?"
        
        with patch('app.rag.query_processor.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "Security policies\nData protection rules"
            mock_llm.return_value.invoke.return_value = mock_response
            
            result = expand_query(original_query, provider="ollama")
            
            assert original_query in result
    
    def test_expand_query_limits_results(self):
        """Test that expansion is limited to max 4 queries."""
        from app.rag.query_processor import expand_query
        
        with patch('app.rag.query_processor.get_llm') as mock_llm:
            # Return many queries
            mock_response = Mock()
            mock_response.content = """Query 1
Query 2
Query 3
Query 4
Query 5
Query 6"""
            mock_llm.return_value.invoke.return_value = mock_response
            
            result = expand_query("test query", provider="ollama")
            
            assert len(result) <= 4
    
    def test_expand_query_handles_llm_error(self):
        """Test graceful handling of LLM errors."""
        from app.rag.query_processor import expand_query
        
        with patch('app.rag.query_processor.get_llm') as mock_llm:
            mock_llm.return_value.invoke.side_effect = Exception("LLM error")
            
            result = expand_query("test query", provider="ollama")
            
            # Should return original query on error
            assert result == ["test query"]
    
    def test_expand_query_cleans_prefixes(self):
        """Test that numbered/bulleted prefixes are cleaned."""
        from app.rag.query_processor import expand_query
        
        with patch('app.rag.query_processor.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = """1. First query variation
2. Second query variation
- Third query variation
* Fourth query variation"""
            mock_llm.return_value.invoke.return_value = mock_response
            
            result = expand_query("original", provider="ollama")
            
            # Check no numbering/bullets in results
            for query in result:
                assert not query.startswith("1.")
                assert not query.startswith("2.")
                assert not query.startswith("-")
                assert not query.startswith("*")
    
    def test_expand_query_filters_short_queries(self):
        """Test that very short queries are filtered out."""
        from app.rag.query_processor import expand_query
        
        with patch('app.rag.query_processor.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = """ok
yes
This is a valid expanded query"""
            mock_llm.return_value.invoke.return_value = mock_response
            
            result = expand_query("original query", provider="ollama")
            
            # Short queries (<=5 chars) should be filtered
            for query in result[1:]:  # Skip original
                assert len(query) > 5


# ============================================================================
# Reranker Unit Tests
# ============================================================================

class TestSimpleReranker:
    """Unit tests for simple keyword-based reranking."""
    
    def test_rerank_empty_chunks(self):
        """Test reranking with empty chunks list."""
        from app.rag.reranker import rerank_chunks_simple
        
        result = rerank_chunks_simple("test query", [], top_k=5)
        
        assert result == []
    
    def test_rerank_returns_top_k(self):
        """Test that reranker returns at most top_k results."""
        from app.rag.reranker import rerank_chunks_simple
        
        chunks = [
            {'text': f'Document chunk {i}', 'score': 0.5}
            for i in range(10)
        ]
        
        result = rerank_chunks_simple("test", chunks, top_k=3)
        
        assert len(result) == 3
    
    def test_rerank_preserves_chunk_data(self):
        """Test that original chunk data is preserved."""
        from app.rag.reranker import rerank_chunks_simple
        
        chunks = [
            {'text': 'Test document about security', 'score': 0.5, 'doc_id': 'doc-1', 'filename': 'test.txt'}
        ]
        
        result = rerank_chunks_simple("security", chunks, top_k=1)
        
        assert result[0]['doc_id'] == 'doc-1'
        assert result[0]['filename'] == 'test.txt'
    
    def test_rerank_adds_scores(self):
        """Test that reranker adds rerank_score and original_score."""
        from app.rag.reranker import rerank_chunks_simple
        
        chunks = [
            {'text': 'Security policy document', 'score': 0.8}
        ]
        
        result = rerank_chunks_simple("security policy", chunks, top_k=1)
        
        assert 'rerank_score' in result[0]
        assert 'original_score' in result[0]
        assert result[0]['original_score'] == 0.8
    
    def test_rerank_boosts_keyword_matches(self):
        """Test that keyword matches boost score."""
        from app.rag.reranker import rerank_chunks_simple
        
        chunks = [
            {'text': 'This document discusses cats and dogs', 'score': 0.8},
            {'text': 'Security policy for data protection', 'score': 0.7},
        ]
        
        result = rerank_chunks_simple("security policy data", chunks, top_k=2)
        
        # The chunk with matching keywords should rank higher
        assert 'security' in result[0]['text'].lower()
    
    def test_rerank_combines_scores(self):
        """Test that combined score uses 70% vector + 30% keyword."""
        from app.rag.reranker import rerank_chunks_simple
        
        chunks = [
            {'text': 'keyword keyword keyword', 'score': 0.5}  # High keyword, medium vector
        ]
        
        result = rerank_chunks_simple("keyword", chunks, top_k=1)
        
        # Score should be between original (0.5) and boosted
        assert result[0]['rerank_score'] >= result[0]['original_score']


class TestLLMReranker:
    """Unit tests for LLM-based reranking."""
    
    def test_llm_rerank_empty_chunks(self):
        """Test LLM reranking with empty chunks."""
        from app.rag.reranker import rerank_chunks_llm
        
        result = rerank_chunks_llm("test", [], provider="ollama")
        
        assert result == []
    
    def test_llm_rerank_parses_scores(self):
        """Test that LLM reranker correctly parses scores."""
        from app.rag.reranker import rerank_chunks_llm
        
        with patch('app.rag.reranker.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "8"  # High relevance score
            mock_llm.return_value.invoke.return_value = mock_response
            
            chunks = [{'text': 'Test content', 'score': 0.5}]
            result = rerank_chunks_llm("test", chunks, provider="ollama", top_k=1)
            
            assert result[0]['rerank_score'] == 8.0
    
    def test_llm_rerank_handles_invalid_scores(self):
        """Test handling of invalid LLM score responses."""
        from app.rag.reranker import rerank_chunks_llm
        
        with patch('app.rag.reranker.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "This is not a number"
            mock_llm.return_value.invoke.return_value = mock_response
            
            chunks = [{'text': 'Test content', 'score': 0.5}]
            result = rerank_chunks_llm("test", chunks, provider="ollama", top_k=1)
            
            # Should default to middle score (5.0) or use original
            assert 'rerank_score' in result[0]
    
    def test_llm_rerank_clamps_scores(self):
        """Test that scores are clamped to 0-10 range."""
        from app.rag.reranker import rerank_chunks_llm
        
        with patch('app.rag.reranker.get_llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "15"  # Out of range
            mock_llm.return_value.invoke.return_value = mock_response
            
            chunks = [{'text': 'Test', 'score': 0.5}]
            result = rerank_chunks_llm("test", chunks, provider="ollama", top_k=1)
            
            assert result[0]['rerank_score'] <= 10


# ============================================================================
# Hybrid Search Unit Tests
# ============================================================================

class TestHybridScoring:
    """Unit tests for hybrid search scoring."""
    
    def test_hybrid_scoring_combines_scores(self):
        """Test that hybrid scoring combines semantic and keyword scores."""
        from app.rag.retrieval import _apply_hybrid_scoring
        
        # Create mock matches
        mock_match = Mock()
        mock_match.score = 0.8
        mock_match.metadata = {'text': 'This is about security policy compliance'}
        
        matches = [mock_match]
        
        result = _apply_hybrid_scoring("security policy", matches)
        
        # Score should be modified
        assert len(result) == 1
        assert hasattr(result[0], '_semantic_score')
        assert hasattr(result[0], '_keyword_score')
    
    def test_hybrid_scoring_removes_stop_words(self):
        """Test that stop words are removed from keyword matching."""
        from app.rag.retrieval import _apply_hybrid_scoring
        
        mock_match = Mock()
        mock_match.score = 0.5
        mock_match.metadata = {'text': 'the is a document'}
        
        # Query with only stop words
        result = _apply_hybrid_scoring("what is the", [mock_match])
        
        # Should still return match (graceful handling)
        assert len(result) == 1
    
    def test_hybrid_scoring_phrase_boost(self):
        """Test that exact phrase matches get boosted."""
        from app.rag.retrieval import _apply_hybrid_scoring
        
        mock_match1 = Mock()
        mock_match1.score = 0.7
        mock_match1.metadata = {'text': 'This document discusses security policy in detail'}
        
        mock_match2 = Mock()
        mock_match2.score = 0.7
        mock_match2.metadata = {'text': 'Security and policy are discussed separately'}
        
        matches = [mock_match1, mock_match2]
        
        result = _apply_hybrid_scoring("security policy", matches)
        
        # Match with exact phrase should rank higher
        assert 'security policy' in result[0].metadata['text'].lower()
    
    def test_hybrid_scoring_sorts_by_combined_score(self):
        """Test that results are sorted by combined score."""
        from app.rag.retrieval import _apply_hybrid_scoring
        
        mock_match1 = Mock()
        mock_match1.score = 0.9
        mock_match1.metadata = {'text': 'Unrelated content here'}
        
        mock_match2 = Mock()
        mock_match2.score = 0.6
        mock_match2.metadata = {'text': 'security policy compliance requirements'}
        
        matches = [mock_match1, mock_match2]
        
        result = _apply_hybrid_scoring("security policy compliance", matches)
        
        # Lower semantic score but higher keyword match should potentially rank higher
        # Results should be sorted
        for i in range(len(result) - 1):
            assert result[i].score >= result[i + 1].score


# ============================================================================
# Citation Class Unit Tests
# ============================================================================

class TestCitationClass:
    """Unit tests for Citation data class."""
    
    def test_citation_creation(self):
        """Test creating a Citation object."""
        from app.rag.retrieval import Citation
        
        citation = Citation(
            doc_id="doc-123",
            filename="test.txt",
            text="Sample citation text",
            score=0.85,
            page_number=5,
            chunk_index=2
        )
        
        assert citation.doc_id == "doc-123"
        assert citation.filename == "test.txt"
        assert citation.text == "Sample citation text"
        assert citation.score == 0.85
        assert citation.page_number == 5
        assert citation.chunk_index == 2
    
    def test_citation_to_dict(self):
        """Test Citation.to_dict() serialization."""
        from app.rag.retrieval import Citation
        
        citation = Citation(
            doc_id="doc-123",
            filename="test.txt",
            text="Sample text",
            score=0.85678,
            chunk_index=0
        )
        
        result = citation.to_dict()
        
        assert isinstance(result, dict)
        assert result['doc_id'] == "doc-123"
        assert result['filename'] == "test.txt"
        assert result['score'] == 0.8568  # Rounded to 4 decimal places
    
    def test_citation_truncates_long_text(self):
        """Test that to_dict truncates long text."""
        from app.rag.retrieval import Citation
        
        long_text = "A" * 500  # 500 characters
        citation = Citation(
            doc_id="doc-1",
            filename="test.txt",
            text=long_text,
            score=0.5,
            chunk_index=0
        )
        
        result = citation.to_dict()
        
        assert len(result['text']) <= 203  # 200 + "..."
        assert result['text'].endswith("...")
    
    def test_citation_optional_page_number(self):
        """Test Citation with no page number."""
        from app.rag.retrieval import Citation
        
        citation = Citation(
            doc_id="doc-1",
            filename="test.txt",
            text="Text",
            score=0.5,
            chunk_index=0
        )
        
        assert citation.page_number is None
        assert citation.to_dict()['page_number'] is None


# ============================================================================
# RAG Options Type Tests
# ============================================================================

class TestRAGOptionsType:
    """Unit tests for RAGOptions TypedDict."""
    
    def test_rag_options_defaults(self):
        """Test RAGOptions with default values."""
        from app.rag.graph import RAGOptions
        
        options: RAGOptions = {
            'query_expansion': False,
            'hybrid_search': False,
            'reranking': False
        }
        
        assert options['query_expansion'] is False
        assert options['hybrid_search'] is False
        assert options['reranking'] is False
    
    def test_rag_options_enabled(self):
        """Test RAGOptions with all enabled."""
        from app.rag.graph import RAGOptions
        
        options: RAGOptions = {
            'query_expansion': True,
            'hybrid_search': True,
            'reranking': True
        }
        
        assert all(options.values())


# ============================================================================
# Schema Validation Tests
# ============================================================================

class TestRAGOptionsSchema:
    """Unit tests for RAGOptions Pydantic schema."""
    
    def test_rag_options_schema_defaults(self):
        """Test RAGOptions schema default values."""
        from app.schemas import RAGOptions
        
        options = RAGOptions()
        
        assert options.query_expansion is False
        assert options.hybrid_search is False
        assert options.reranking is False
    
    def test_rag_options_schema_with_values(self):
        """Test RAGOptions schema with explicit values."""
        from app.schemas import RAGOptions
        
        options = RAGOptions(
            query_expansion=True,
            hybrid_search=True,
            reranking=False
        )
        
        assert options.query_expansion is True
        assert options.hybrid_search is True
        assert options.reranking is False
    
    def test_chat_request_with_rag_options(self):
        """Test ChatRequest includes RAGOptions."""
        from app.schemas import ChatRequest, RAGOptions
        
        request = ChatRequest(
            user_id="user-123",
            provider="ollama",
            question="What is the leave policy?",
            rag_options=RAGOptions(query_expansion=True)
        )
        
        assert request.rag_options.query_expansion is True
        assert request.rag_options.hybrid_search is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
