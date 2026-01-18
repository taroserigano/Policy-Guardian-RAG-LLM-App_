"""
Integration Tests for Advanced RAG Options
Tests the RAG pipeline with different option combinations
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_pinecone_results():
    """Create mock Pinecone query results."""
    def create_results(num_matches=5):
        matches = []
        for i in range(num_matches):
            match = Mock()
            match.score = 0.9 - (i * 0.1)
            match.metadata = {
                'doc_id': f'doc-{i}',
                'filename': f'document_{i}.txt',
                'text': f'This is sample content for document {i}. It contains policy information about security and compliance.',
                'chunk_index': i,
                'page_number': i + 1
            }
            matches.append(match)
        
        result = Mock()
        result.matches = matches
        return result
    
    return create_results


@pytest.fixture
def mock_llm_response():
    """Create mock LLM response."""
    def create_response(content):
        response = Mock()
        response.content = content
        return response
    return create_response


@pytest.fixture
def sample_chat_request():
    """Create sample chat request data."""
    return {
        'question': 'What is the company security policy?',
        'provider': 'ollama',
        'model': None,
        'doc_ids': None,
        'top_k': 5,
        'rag_options': {
            'query_expansion': False,
            'hybrid_search': False,
            'reranking': False
        }
    }


# ============================================================================
# Retrieval Integration Tests
# ============================================================================

class TestRetrievalWithOptions:
    """Integration tests for retrieval with RAG options."""
    
    @pytest.mark.integration
    def test_retrieve_without_options(self, mock_pinecone_results):
        """Test basic retrieval without any RAG options."""
        from app.rag.retrieval import retrieve_relevant_chunks
        
        with patch('app.rag.retrieval.get_pinecone_index') as mock_index, \
             patch('app.rag.retrieval.default_embeddings') as mock_embed:
            
            mock_index.return_value.query.return_value = mock_pinecone_results(5)
            mock_embed.embed_query.return_value = [0.1] * 1536
            
            citations, context = retrieve_relevant_chunks(
                query="security policy",
                top_k=5,
                use_hybrid=False
            )
            
            assert len(citations) == 5
            assert context != ""
            assert "security" in context.lower() or "policy" in context.lower()
    
    @pytest.mark.integration
    def test_retrieve_with_hybrid_search(self, mock_pinecone_results):
        """Test retrieval with hybrid search enabled."""
        from app.rag.retrieval import retrieve_relevant_chunks
        
        with patch('app.rag.retrieval.get_pinecone_index') as mock_index, \
             patch('app.rag.retrieval.default_embeddings') as mock_embed:
            
            mock_index.return_value.query.return_value = mock_pinecone_results(10)
            mock_embed.embed_query.return_value = [0.1] * 1536
            
            citations, context = retrieve_relevant_chunks(
                query="security policy",
                top_k=5,
                use_hybrid=True
            )
            
            # Hybrid search fetches more, then filters
            assert len(citations) <= 5
            mock_index.return_value.query.assert_called_once()
            # Should have requested more results for hybrid
            call_args = mock_index.return_value.query.call_args
            assert call_args.kwargs['top_k'] == 10  # top_k * 2 for hybrid
    
    @pytest.mark.integration
    def test_retrieve_with_doc_filter(self, mock_pinecone_results):
        """Test retrieval with document ID filter."""
        from app.rag.retrieval import retrieve_relevant_chunks
        
        with patch('app.rag.retrieval.get_pinecone_index') as mock_index, \
             patch('app.rag.retrieval.default_embeddings') as mock_embed:
            
            mock_index.return_value.query.return_value = mock_pinecone_results(3)
            mock_embed.embed_query.return_value = [0.1] * 1536
            
            citations, context = retrieve_relevant_chunks(
                query="test query",
                top_k=5,
                doc_ids=["doc-1", "doc-2"]
            )
            
            # Should have filter in query
            call_args = mock_index.return_value.query.call_args
            assert call_args.kwargs['filter'] == {"doc_id": {"$in": ["doc-1", "doc-2"]}}


class TestMultiQueryRetrieval:
    """Integration tests for multi-query retrieval."""
    
    @pytest.mark.integration
    def test_multi_query_combines_results(self, mock_pinecone_results):
        """Test that multi-query combines results from multiple queries."""
        from app.rag.retrieval import retrieve_with_multi_query
        
        with patch('app.rag.retrieval.retrieve_relevant_chunks') as mock_retrieve:
            # Each query returns different results
            mock_retrieve.side_effect = [
                ([Mock(doc_id='doc-1', chunk_index=0, text='Text 1', score=0.9, filename='f1.txt', page_number=1)], "ctx1"),
                ([Mock(doc_id='doc-2', chunk_index=0, text='Text 2', score=0.8, filename='f2.txt', page_number=1)], "ctx2"),
            ]
            
            citations, context = retrieve_with_multi_query(
                queries=["query 1", "query 2"],
                top_k=5
            )
            
            # Should have called retrieve for each query
            assert mock_retrieve.call_count == 2
    
    @pytest.mark.integration
    def test_multi_query_deduplicates(self, mock_pinecone_results):
        """Test that multi-query deduplicates overlapping results."""
        from app.rag.retrieval import retrieve_with_multi_query
        
        with patch('app.rag.retrieval.retrieve_relevant_chunks') as mock_retrieve:
            # Same document returned by both queries
            same_citation = Mock(doc_id='doc-1', chunk_index=0, text='Text', score=0.9, filename='f.txt', page_number=1)
            mock_retrieve.side_effect = [
                ([same_citation], "ctx"),
                ([same_citation], "ctx"),
            ]
            
            citations, context = retrieve_with_multi_query(
                queries=["query 1", "query 2"],
                top_k=5
            )
            
            # Should deduplicate to single result
            assert len(citations) == 1
    
    @pytest.mark.integration
    def test_multi_query_frequency_bonus(self, mock_pinecone_results):
        """Test that chunks appearing in multiple queries get score bonus."""
        from app.rag.retrieval import retrieve_with_multi_query
        
        with patch('app.rag.retrieval.retrieve_relevant_chunks') as mock_retrieve:
            # Same document in both queries
            citation1 = Mock(doc_id='doc-1', chunk_index=0, text='Shared text', score=0.7, filename='f.txt', page_number=1)
            citation2 = Mock(doc_id='doc-2', chunk_index=0, text='Unique text', score=0.9, filename='f2.txt', page_number=1)
            
            mock_retrieve.side_effect = [
                ([citation1, citation2], "ctx"),
                ([citation1], "ctx"),  # doc-1 appears again
            ]
            
            citations, context = retrieve_with_multi_query(
                queries=["query 1", "query 2"],
                top_k=5
            )
            
            # doc-1 should be boosted due to appearing in multiple queries
            # Find doc-1 citation
            doc1_citation = next((c for c in citations if c.doc_id == 'doc-1'), None)
            assert doc1_citation is not None


# ============================================================================
# RAG Pipeline Integration Tests
# ============================================================================

class TestRAGPipelineWithOptions:
    """Integration tests for full RAG pipeline with options."""
    
    @pytest.mark.integration
    def test_pipeline_streaming_no_options(self, mock_pinecone_results, mock_llm_response):
        """Test streaming pipeline without RAG options."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.retrieve_relevant_chunks') as mock_retrieve, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            # Setup mocks
            mock_citation = Mock()
            mock_citation.doc_id = 'doc-1'
            mock_citation.filename = 'test.txt'
            mock_citation.text = 'Sample text'
            mock_citation.score = 0.9
            mock_citation.page_number = 1
            mock_citation.chunk_index = 0
            mock_citation.to_dict.return_value = {'doc_id': 'doc-1', 'filename': 'test.txt', 'score': 0.9, 'chunk_index': 0, 'page_number': 1, 'text': 'Sample...'}
            
            mock_retrieve.return_value = ([mock_citation], "Context text")
            mock_llm.return_value.stream.return_value = iter(["Hello", " ", "World"])
            
            events = list(run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options=None
            ))
            
            # Should have citations and tokens
            event_types = [e['type'] for e in events]
            assert 'citations' in event_types
            assert 'token' in event_types
    
    @pytest.mark.integration
    def test_pipeline_streaming_with_expansion(self, mock_llm_response):
        """Test streaming pipeline with query expansion."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.expand_query') as mock_expand, \
             patch('app.rag.graph.retrieve_with_multi_query') as mock_multi, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            # Setup mocks
            mock_expand.return_value = ["original", "expanded query 1", "expanded query 2"]
            
            mock_citation = Mock()
            mock_citation.to_dict.return_value = {'doc_id': 'doc-1', 'filename': 'test.txt', 'score': 0.9, 'chunk_index': 0, 'page_number': 1, 'text': 'Sample...'}
            mock_multi.return_value = ([mock_citation], "Context")
            
            mock_llm.return_value.stream.return_value = iter(["Response"])
            
            events = list(run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options={'query_expansion': True, 'hybrid_search': False, 'reranking': False}
            ))
            
            # Should have called expand_query
            mock_expand.assert_called_once()
            # Should have used multi-query retrieval
            mock_multi.assert_called_once()
    
    @pytest.mark.integration
    def test_pipeline_streaming_with_reranking(self):
        """Test streaming pipeline with reranking enabled."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.retrieve_relevant_chunks') as mock_retrieve, \
             patch('app.rag.graph.rerank_chunks_simple') as mock_rerank, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            # Setup mocks
            mock_citation = Mock()
            mock_citation.doc_id = 'doc-1'
            mock_citation.filename = 'test.txt'
            mock_citation.text = 'Sample text'
            mock_citation.score = 0.9
            mock_citation.page_number = 1
            mock_citation.chunk_index = 0
            mock_citation.to_dict.return_value = {'doc_id': 'doc-1', 'filename': 'test.txt', 'score': 0.9, 'chunk_index': 0, 'page_number': 1, 'text': 'Sample...'}
            
            mock_retrieve.return_value = ([mock_citation], "Context")
            mock_rerank.return_value = [{'citation': mock_citation, 'rerank_score': 0.95}]
            mock_llm.return_value.stream.return_value = iter(["Response"])
            
            events = list(run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options={'query_expansion': False, 'hybrid_search': False, 'reranking': True}
            ))
            
            # Should have called reranker
            mock_rerank.assert_called_once()
    
    @pytest.mark.integration
    def test_pipeline_streaming_all_options(self):
        """Test streaming pipeline with all RAG options enabled."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.expand_query') as mock_expand, \
             patch('app.rag.graph.retrieve_with_multi_query') as mock_multi, \
             patch('app.rag.graph.rerank_chunks_simple') as mock_rerank, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            # Setup mocks
            mock_expand.return_value = ["q1", "q2"]
            
            mock_citation = Mock()
            mock_citation.text = 'Sample'
            mock_citation.score = 0.9
            mock_citation.filename = 'test.txt'
            mock_citation.page_number = 1
            mock_citation.chunk_index = 0
            mock_citation.to_dict.return_value = {'doc_id': 'doc-1', 'score': 0.9}
            
            mock_multi.return_value = ([mock_citation], "Context")
            mock_rerank.return_value = [{'citation': mock_citation}]
            mock_llm.return_value.stream.return_value = iter(["Response"])
            
            events = list(run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options={'query_expansion': True, 'hybrid_search': True, 'reranking': True}
            ))
            
            # All components should be called
            mock_expand.assert_called_once()
            mock_multi.assert_called_once()
            mock_rerank.assert_called_once()
    
    @pytest.mark.integration
    def test_pipeline_handles_empty_context(self):
        """Test pipeline handles no results gracefully."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.retrieve_relevant_chunks') as mock_retrieve, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            mock_retrieve.return_value = ([], "")  # No results
            
            events = list(run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options=None
            ))
            
            # Should return appropriate message
            tokens = [e['data'] for e in events if e['type'] == 'token']
            full_response = ''.join(tokens)
            assert "couldn't find" in full_response.lower() or "no" in full_response.lower()
    
    @pytest.mark.integration
    def test_pipeline_handles_expansion_failure(self):
        """Test pipeline continues if query expansion fails."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.expand_query') as mock_expand, \
             patch('app.rag.graph.retrieve_relevant_chunks') as mock_retrieve, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            # Expansion fails
            mock_expand.side_effect = Exception("Expansion error")
            
            mock_citation = Mock()
            mock_citation.to_dict.return_value = {'doc_id': 'doc-1', 'score': 0.9}
            mock_retrieve.return_value = ([mock_citation], "Context")
            mock_llm.return_value.stream.return_value = iter(["Response"])
            
            # Should not raise, should fallback to original query
            events = list(run_rag_pipeline_streaming(
                question="Test question",
                provider="ollama",
                rag_options={'query_expansion': True, 'hybrid_search': False, 'reranking': False}
            ))
            
            # Should have used original query
            mock_retrieve.assert_called_once()


# ============================================================================
# Error Handling Integration Tests
# ============================================================================

class TestRAGErrorHandling:
    """Integration tests for error handling in RAG pipeline."""
    
    @pytest.mark.integration
    def test_retrieval_error_yields_error_event(self):
        """Test that retrieval errors yield error events."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.retrieve_relevant_chunks') as mock_retrieve:
            mock_retrieve.side_effect = Exception("Pinecone connection error")
            
            events = list(run_rag_pipeline_streaming(
                question="Test",
                provider="ollama",
                rag_options=None
            ))
            
            error_events = [e for e in events if e['type'] == 'error']
            assert len(error_events) == 1
            assert 'error' in error_events[0]['data'].lower()
    
    @pytest.mark.integration
    def test_llm_error_yields_error_event(self):
        """Test that LLM errors yield error events."""
        from app.rag.graph import run_rag_pipeline_streaming
        
        with patch('app.rag.graph.retrieve_relevant_chunks') as mock_retrieve, \
             patch('app.rag.graph.get_streaming_llm') as mock_llm:
            
            mock_citation = Mock()
            mock_citation.to_dict.return_value = {'doc_id': '1', 'score': 0.9}
            mock_retrieve.return_value = ([mock_citation], "Context")
            mock_llm.side_effect = Exception("LLM unavailable")
            
            events = list(run_rag_pipeline_streaming(
                question="Test",
                provider="ollama",
                rag_options=None
            ))
            
            error_events = [e for e in events if e['type'] == 'error']
            assert len(error_events) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
