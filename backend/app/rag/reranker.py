"""
Reranking module for improving retrieval relevance.
Uses cross-encoder models or LLM-based reranking.
"""
from typing import List, Tuple
from dataclasses import dataclass

from app.core.logging import get_logger
from app.rag.llms import get_llm

logger = get_logger(__name__)


@dataclass
class RankedChunk:
    """A chunk with its reranking score."""
    text: str
    original_score: float
    rerank_score: float
    metadata: dict


def rerank_chunks_llm(
    query: str,
    chunks: List[dict],
    provider: str = "ollama",
    model: str = None,
    top_k: int = 5
) -> List[dict]:
    """
    Rerank retrieved chunks using LLM-based scoring.
    
    This method asks the LLM to score each chunk's relevance to the query,
    then returns chunks sorted by the new scores.
    
    Args:
        query: User's question
        chunks: List of chunk dictionaries with 'text', 'score', and metadata
        provider: LLM provider for reranking
        model: Optional specific model
        top_k: Number of top chunks to return after reranking
    
    Returns:
        Reranked list of chunks (top_k)
    """
    if not chunks:
        return []
    
    logger.info(f"Reranking {len(chunks)} chunks with LLM")
    
    try:
        llm = get_llm(provider=provider, model=model)
        
        reranked = []
        
        for chunk in chunks:
            text = chunk.get('text', '')[:500]  # Limit text length
            
            scoring_prompt = f"""Rate how relevant this text passage is to answering the question.
Score from 0 to 10, where:
- 0 = completely irrelevant
- 5 = somewhat relevant
- 10 = highly relevant and directly answers the question

Question: {query}

Text passage:
{text}

Output ONLY a number from 0 to 10, nothing else:"""

            messages = [
                {"role": "system", "content": "You are a relevance scorer. Output only a number from 0 to 10."},
                {"role": "user", "content": scoring_prompt}
            ]
            
            try:
                if hasattr(llm, 'invoke'):
                    response = llm.invoke(messages)
                    if hasattr(response, 'content'):
                        score_text = response.content.strip()
                    else:
                        score_text = str(response).strip()
                else:
                    score_text = llm.generate(messages).strip()
                
                # Parse score
                import re
                score_match = re.search(r'\d+(?:\.\d+)?', score_text)
                if score_match:
                    rerank_score = min(10, max(0, float(score_match.group())))
                else:
                    rerank_score = 5.0  # Default to middle score
                    
            except Exception as e:
                logger.warning(f"Error scoring chunk: {e}")
                rerank_score = chunk.get('score', 0.5) * 10  # Use original score
            
            reranked.append({
                **chunk,
                'rerank_score': rerank_score,
                'original_score': chunk.get('score', 0)
            })
        
        # Sort by rerank score descending
        reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        logger.info(f"Reranking complete, returning top {top_k} chunks")
        return reranked[:top_k]
        
    except Exception as e:
        logger.error(f"Error in reranking: {e}")
        # Return original chunks on error
        return chunks[:top_k]


def rerank_chunks_simple(
    query: str,
    chunks: List[dict],
    top_k: int = 5
) -> List[dict]:
    """
    Simple reranking using keyword overlap scoring.
    
    Faster than LLM-based reranking, combines vector similarity
    with keyword overlap for better relevance.
    
    Args:
        query: User's question
        chunks: List of chunk dictionaries
        top_k: Number of top chunks to return
    
    Returns:
        Reranked list of chunks
    """
    if not chunks:
        return []
    
    logger.info(f"Simple reranking {len(chunks)} chunks")
    
    # Extract query keywords
    query_words = set(query.lower().split())
    
    reranked = []
    for chunk in chunks:
        text = chunk.get('text', '').lower()
        text_words = set(text.split())
        
        # Calculate keyword overlap
        overlap = len(query_words & text_words)
        keyword_score = overlap / max(len(query_words), 1)
        
        # Combine with original score (70% vector, 30% keyword)
        original = chunk.get('score', 0)
        combined_score = (original * 0.7) + (keyword_score * 0.3)
        
        reranked.append({
            **chunk,
            'rerank_score': combined_score,
            'original_score': original
        })
    
    # Sort by combined score
    reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
    
    return reranked[:top_k]


def mmr_rerank(
    query_embedding: List[float],
    chunks: List[dict],
    chunk_embeddings: List[List[float]],
    top_k: int = 5,
    diversity: float = 0.3
) -> List[dict]:
    """
    Maximum Marginal Relevance reranking for diversity.
    
    Balances relevance to query with diversity among selected chunks.
    
    Args:
        query_embedding: Query vector
        chunks: List of chunk dictionaries
        chunk_embeddings: Corresponding embeddings for chunks
        top_k: Number of chunks to select
        diversity: Lambda parameter (0=pure relevance, 1=pure diversity)
    
    Returns:
        MMR-reranked list of chunks
    """
    import numpy as np
    
    if not chunks or not chunk_embeddings:
        return chunks[:top_k] if chunks else []
    
    logger.info(f"MMR reranking {len(chunks)} chunks with diversity={diversity}")
    
    query_vec = np.array(query_embedding)
    doc_vecs = np.array(chunk_embeddings)
    
    # Normalize vectors
    query_vec = query_vec / np.linalg.norm(query_vec)
    doc_vecs = doc_vecs / np.linalg.norm(doc_vecs, axis=1, keepdims=True)
    
    # Compute query-document similarities
    query_sims = np.dot(doc_vecs, query_vec)
    
    selected = []
    selected_indices = set()
    
    for _ in range(min(top_k, len(chunks))):
        best_score = -float('inf')
        best_idx = -1
        
        for i in range(len(chunks)):
            if i in selected_indices:
                continue
            
            # Relevance to query
            relevance = query_sims[i]
            
            # Max similarity to already selected docs
            if selected_indices:
                selected_vecs = doc_vecs[list(selected_indices)]
                redundancy = np.max(np.dot(selected_vecs, doc_vecs[i]))
            else:
                redundancy = 0
            
            # MMR score
            mmr_score = (1 - diversity) * relevance - diversity * redundancy
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
        
        if best_idx >= 0:
            selected_indices.add(best_idx)
            selected.append({
                **chunks[best_idx],
                'mmr_score': best_score,
                'original_score': chunks[best_idx].get('score', 0)
            })
    
    return selected
