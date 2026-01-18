"""
Query processing module for advanced RAG features.
Supports query expansion/rewriting for better retrieval coverage.
"""
from typing import List
import re

from app.core.logging import get_logger
from app.rag.llms import get_llm

logger = get_logger(__name__)


def expand_query(query: str, provider: str = "ollama", model: str = None) -> List[str]:
    """
    Expand a user query into multiple search queries for better coverage.
    
    Uses LLM to generate alternative phrasings and related queries.
    
    Args:
        query: Original user question
        provider: LLM provider to use for expansion
        model: Optional specific model name
    
    Returns:
        List of queries including original plus expanded versions
    """
    logger.info(f"Expanding query: {query[:50]}...")
    
    # Always include original query
    queries = [query]
    
    try:
        llm = get_llm(provider=provider, model=model)
        
        expansion_prompt = f"""Generate 2-3 alternative search queries for the following question. 
These should be variations that might help find relevant information in policy/legal documents.

Original question: {query}

Rules:
- Keep queries concise and focused
- Use different phrasings and synonyms
- Include relevant legal/policy terminology if applicable
- Return ONLY the queries, one per line, no numbering or bullets

Alternative queries:"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates search query variations. Output only the queries, one per line."},
            {"role": "user", "content": expansion_prompt}
        ]
        
        if hasattr(llm, 'invoke'):
            response = llm.invoke(messages)
            if hasattr(response, 'content'):
                expanded_text = response.content
            else:
                expanded_text = response
        else:
            expanded_text = llm.generate(messages)
        
        # Parse expanded queries
        for line in expanded_text.strip().split('\n'):
            line = line.strip()
            # Clean up common prefixes
            line = re.sub(r'^[\d\.\-\*\•]+\s*', '', line)
            if line and line != query and len(line) > 5:
                queries.append(line)
        
        # Limit to max 4 queries total
        queries = queries[:4]
        
        logger.info(f"Expanded to {len(queries)} queries")
        return queries
        
    except Exception as e:
        logger.error(f"Error expanding query: {e}")
        # Return original query on error
        return [query]


def rewrite_query(query: str, provider: str = "ollama", model: str = None) -> str:
    """
    Rewrite a user query to be more effective for retrieval.
    
    Clarifies ambiguous terms and adds context for better search.
    
    Args:
        query: Original user question
        provider: LLM provider to use
        model: Optional specific model name
    
    Returns:
        Rewritten query optimized for search
    """
    logger.info(f"Rewriting query: {query[:50]}...")
    
    try:
        llm = get_llm(provider=provider, model=model)
        
        rewrite_prompt = f"""Rewrite the following question to be more effective for searching policy and legal documents.
Make it clearer and more specific while preserving the original intent.

Original question: {query}

Rewritten question (output ONLY the rewritten question, nothing else):"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that rewrites questions for better search. Output only the rewritten question."},
            {"role": "user", "content": rewrite_prompt}
        ]
        
        if hasattr(llm, 'invoke'):
            response = llm.invoke(messages)
            if hasattr(response, 'content'):
                rewritten = response.content.strip()
            else:
                rewritten = str(response).strip()
        else:
            rewritten = llm.generate(messages).strip()
        
        # Clean up any quotes or extra formatting
        rewritten = rewritten.strip('"\'')
        
        logger.info(f"Rewritten query: {rewritten[:50]}...")
        return rewritten if rewritten else query
        
    except Exception as e:
        logger.error(f"Error rewriting query: {e}")
        return query


def extract_keywords(query: str) -> List[str]:
    """
    Extract important keywords from a query for hybrid search.
    
    Args:
        query: User question
    
    Returns:
        List of important keywords
    """
    # Common stop words to filter out
    stop_words = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'shall', 'need',
        'what', 'which', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        'i', 'me', 'my', 'we', 'us', 'our', 'you', 'your',
        'and', 'or', 'but', 'if', 'then', 'else', 'for', 'of', 'to', 'from',
        'in', 'on', 'at', 'by', 'with', 'about', 'as', 'into', 'through'
    }
    
    # Tokenize and filter
    words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords
