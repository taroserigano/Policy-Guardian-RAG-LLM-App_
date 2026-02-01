"""
LangGraph-based RAG workflow.
Orchestrates retrieval and generation with proper state management.
Supports both regular and streaming responses with advanced RAG options.
"""
from typing import TypedDict, List, Dict, Any, Optional, Generator
from langgraph.graph import StateGraph, END

from app.core.logging import get_logger
from app.rag.retrieval import retrieve_relevant_chunks, retrieve_with_multi_query, Citation
from app.rag.llms import get_llm, get_streaming_llm
from app.rag.query_processor import expand_query, extract_keywords
from app.rag.reranker import rerank_chunks_simple

logger = get_logger(__name__)
logger.info("🔧 GRAPH.PY LOADED WITH LANGCHAIN MESSAGE FIX - VERSION 2")


class RAGOptions(TypedDict, total=False):
    """Advanced RAG processing options."""
    query_expansion: bool
    hybrid_search: bool
    reranking: bool


class RAGState(TypedDict):
    """State for RAG workflow."""
    question: str
    provider: str
    model: Optional[str]
    doc_ids: Optional[List[str]]
    top_k: int
    rag_options: Optional[RAGOptions]
    citations: List[Citation]
    context: str
    answer: str
    error: Optional[str]


def retrieval_node(state: RAGState) -> Dict[str, Any]:
    """
    Retrieval node: Query Pinecone for relevant chunks.
    
    Args:
        state: Current RAG state
    
    Returns:
        Updated state with citations and context
    """
    try:
        logger.info("Executing retrieval node")
        
        citations, context = retrieve_relevant_chunks(
            query=state["question"],
            top_k=state.get("top_k", 5),
            doc_ids=state.get("doc_ids")
        )
        
        return {
            "citations": citations,
            "context": context,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"Error in retrieval node: {e}")
        return {
            "citations": [],
            "context": "",
            "error": f"Retrieval error: {str(e)}"
        }


def generation_node(state: RAGState) -> Dict[str, Any]:
    """
    Generation node: Use LLM to answer question based on context.
    
    Args:
        state: Current RAG state with context
    
    Returns:
        Updated state with answer
    """
    try:
        logger.info("Executing generation node")
        
        # Check if we have context
        if not state.get("context"):
            return {
                "answer": "I couldn't find any relevant information in the documents to answer your question.",
                "error": None
            }
        
        # Build system prompt for legal/compliance tone
        system_prompt = """You are an AI assistant specializing in organizational policy and compliance document analysis.

Your role is to:
1. Answer questions ONLY based on the provided context from official policy documents
2. Quote specific policy sections, effective dates, and document names when citing requirements
3. Clearly distinguish between:
   - What the policy explicitly states
   - What is not covered in the provided context
4. Flag important qualifiers like "must," "should," "may," and "unless" when they appear
5. If the answer depends on factors not in the context (e.g., jurisdiction, role, employment status), note that and suggest consulting HR or legal for specifics
6. Use clear, professional language; avoid legal jargon unless it appears in the source
7. Never speculate or provide information not present in the context

When answering:
- Lead with the direct answer if clear
- Cite the specific policy or section (e.g., "Per the Remote Work Policy, section 2.1...")
- Note relevant effective dates or version numbers when available
- If multiple documents address the topic, briefly reconcile them or note which is most relevant

Answer the user's question using only the information provided below."""

        # Build user prompt with context
        user_prompt = f"""Context from documents:

{state['context']}

---

Question: {state['question']}

Please provide a clear, accurate answer based only on the context above. If the context doesn't contain enough information to answer the question, say so."""

        # Get LLM and generate response
        llm = get_llm(
            provider=state["provider"],
            model=state.get("model")
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Handle different LLM interfaces
        if hasattr(llm, 'invoke'):
            response = llm.invoke(messages)
            # Handle both string and message object responses
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = response
        else:
            # Fallback for custom implementations
            answer = llm.generate(messages)
        
        return {
            "answer": answer,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"Error in generation node: {e}")
        return {
            "answer": "",
            "error": f"Generation error: {str(e)}"
        }


def create_rag_graph() -> StateGraph:
    """
    Create the RAG workflow graph.
    
    Flow:
        START -> retrieval -> generation -> END
    
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("generation", generation_node)
    
    # Define edges
    workflow.set_entry_point("retrieval")
    workflow.add_edge("retrieval", "generation")
    workflow.add_edge("generation", END)
    
    # Compile
    return workflow.compile()


# Create singleton graph instance
rag_graph = create_rag_graph()


def run_rag_pipeline(
    question: str,
    provider: str,
    model: Optional[str] = None,
    doc_ids: Optional[List[str]] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Run the complete RAG pipeline.
    
    Args:
        question: User's question
        provider: LLM provider ("ollama", "openai", "anthropic")
        model: Optional specific model name
        doc_ids: Optional list of document IDs to restrict search
        top_k: Number of chunks to retrieve
    
    Returns:
        Dictionary with answer, citations, and model info
    """
    logger.info(f"Running RAG pipeline with provider={provider}, top_k={top_k}")
    
    # Initialize state
    initial_state: RAGState = {
        "question": question,
        "provider": provider,
        "model": model,
        "doc_ids": doc_ids,
        "top_k": top_k,
        "citations": [],
        "context": "",
        "answer": "",
        "error": None
    }
    
    # Execute graph
    final_state = rag_graph.invoke(initial_state)
    
    # Check for errors
    if final_state.get("error"):
        raise Exception(final_state["error"])
    
    # Format response
    return {
        "answer": final_state["answer"],
        "citations": [citation.to_dict() for citation in final_state["citations"]],
        "model": {
            "provider": provider,
            "name": model or "default"
        }
    }


def run_rag_pipeline_streaming(
    question: str,
    provider: str,
    model: Optional[str] = None,
    doc_ids: Optional[List[str]] = None,
    top_k: int = 5,
    rag_options: Optional[Dict] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Run the RAG pipeline with streaming response and advanced RAG options.
    Includes proper memory cleanup to prevent leaks.
    
    Args:
        question: User's question
        provider: LLM provider ("ollama", "openai", "anthropic")
        model: Optional specific model name
        doc_ids: Optional list of document IDs to restrict search
        top_k: Number of chunks to retrieve
        rag_options: Optional dict with keys:
            - query_expansion: bool - expand query into multiple variations
            - hybrid_search: bool - use keyword + semantic search
            - reranking: bool - rerank results for better relevance
    
    Yields:
        Dictionary events with type and data:
        - {"type": "token", "data": "..."}
        - {"type": "citations", "data": [...]}
        - {"type": "model", "data": {"provider": "...", "name": "..."}}
    """
    # Initialize variables for cleanup
    citations = []
    context = ""
    queries = []
    chunks_for_rerank = []
    messages = []
    context_parts = []
    
    try:
        if rag_options is None:
            rag_options = {}
        
        use_expansion = rag_options.get('query_expansion', False)
        use_hybrid = rag_options.get('hybrid_search', False)
        use_reranking = rag_options.get('reranking', False)
        use_auto_rewrite = rag_options.get('auto_rewrite', False)
        use_cross_encoder = rag_options.get('cross_encoder', False)
        
        logger.info(f"Running streaming RAG pipeline with provider={provider}, top_k={top_k}, "
                    f"expansion={use_expansion}, hybrid={use_hybrid}, reranking={use_reranking}, "
                    f"auto_rewrite={use_auto_rewrite}, cross_encoder={use_cross_encoder}")
        
        # Step 1: Query processing (expansion or rewrite if enabled)
        try:
            processed_question = question
            
            # Auto-rewrite improves query for better retrieval
            if use_auto_rewrite:
                from app.rag.query_processor import rewrite_query
                processed_question = rewrite_query(question, provider=provider, model=model)
                logger.info(f"Query rewritten: {processed_question[:100]}...")
            
            if use_expansion:
                queries = expand_query(processed_question, provider=provider, model=model)
                logger.info(f"Query expanded to {len(queries)} variations")
            else:
                queries = [processed_question]
        except Exception as e:
            logger.warning(f"Query processing failed, using original: {e}")
            queries = [question]
        
        # Step 2: Retrieve relevant chunks
        try:
            if len(queries) > 1:
                # Multi-query retrieval
                citations, context = retrieve_with_multi_query(
                    queries=queries,
                    top_k=top_k * 2 if use_reranking else top_k,  # Get more for reranking
                    doc_ids=doc_ids,
                    use_hybrid=use_hybrid
                )
            else:
                # Single query retrieval
                citations, context = retrieve_relevant_chunks(
                    query=question,
                    top_k=top_k * 2 if use_reranking else top_k,
                    doc_ids=doc_ids,
                    use_hybrid=use_hybrid
                )
            
            # Step 3: Reranking if enabled
            if (use_reranking or use_cross_encoder) and citations:
                logger.info(f"Applying reranking to results (cross_encoder={use_cross_encoder})")
                chunks_for_rerank = [
                    {'text': c.text, 'score': c.score, 'citation': c}
                    for c in citations
                ]
                
                if use_cross_encoder:
                    # Use more accurate cross-encoder (LLM-based deep scoring)
                    from app.rag.reranker import rerank_chunks_llm
                    reranked = rerank_chunks_llm(question, chunks_for_rerank, provider=provider, model=model, top_k=top_k)
                else:
                    # Use simpler reranking
                    reranked = rerank_chunks_simple(question, chunks_for_rerank, top_k=top_k)
                
                citations = [r['citation'] for r in reranked]
                
                # Rebuild context from reranked citations
                context_parts = []
                for citation in citations:
                    source_info = f"Source: {citation.filename}"
                    if citation.page_number:
                        source_info += f", page {citation.page_number}"
                    context_parts.append(f"[{source_info}]\n{citation.text}\n")
                context = "\n---\n".join(context_parts)
            
            # Yield citations early so frontend can display them
            yield {
                "type": "citations",
                "data": [citation.to_dict() for citation in citations]
            }
            
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            yield {"type": "error", "data": f"Retrieval error: {str(e)}"}
            return
        
        # Step 2: Check if we have context
        if not context:
            yield {
                "type": "token", 
                "data": "I couldn't find any relevant information in the documents to answer your question."
            }
            yield {"type": "model", "data": {"provider": provider, "name": model or "default"}}
            return
        
        # Step 3: Build prompts
        system_prompt = """You are an AI assistant specializing in organizational policy and compliance document analysis.

Your role is to:
1. Answer questions ONLY based on the provided context from official policy documents
2. Quote specific policy sections, effective dates, and document names when citing requirements
3. Clearly distinguish between:
   - What the policy explicitly states
   - What is not covered in the provided context
4. Flag important qualifiers like "must," "should," "may," and "unless" when they appear
5. If the answer depends on factors not in the context (e.g., jurisdiction, role, employment status), note that and suggest consulting HR or legal for specifics
6. Use clear, professional language; avoid legal jargon unless it appears in the source
7. Never speculate or provide information not present in the context

When answering:
- Lead with the direct answer if clear
- Cite the specific policy or section (e.g., "Per the Remote Work Policy, section 2.1...")
- Note relevant effective dates or version numbers when available
- If multiple documents address the topic, briefly reconcile them or note which is most relevant

Answer the user's question using only the information provided below."""

        user_prompt = f"""Context from documents:

{context}

---

Question: {question}

Please provide a clear, accurate answer based only on the context above. If the context doesn't contain enough information to answer the question, say so."""

        # Build messages - format depends on provider
        if provider == "ollama":
            # Ollama accepts dict format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        else:
            # OpenAI/Anthropic need LangChain message objects
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
        
        # Step 4: Stream LLM response
        try:
            logger.info(f"Starting LLM streaming with provider={provider}, model={model}")
            logger.debug(f"Messages: {messages}")
            
            llm = get_streaming_llm(provider=provider, model=model)
            logger.info(f"LLM instance created: {type(llm)}")
            
            token_count = 0
            if provider == "ollama":
                # Use custom stream method for Ollama
                for token in llm.stream(messages):
                    token_count += 1
                    yield {"type": "token", "data": token}
                logger.info(f"Ollama streamed {token_count} tokens")
            else:
                # Use LangChain stream for OpenAI/Anthropic
                logger.info(f"Starting LangChain stream for {provider}")
                logger.info(f"About to call llm.stream() with {len(messages)} messages")
                try:
                    for chunk in llm.stream(messages):
                        token_count += 1
                        logger.debug(f"Chunk #{token_count}: {chunk}")
                        if hasattr(chunk, 'content') and chunk.content:
                            yield {"type": "token", "data": chunk.content}
                        elif hasattr(chunk, 'content'):
                            logger.warning(f"Chunk has empty content: {chunk}")
                        else:
                            logger.warning(f"Chunk has no content attribute: {chunk}")
                    logger.info(f"LangChain streamed {token_count} tokens total")
                except Exception as stream_err:
                    logger.error(f"Error during streaming: {stream_err}", exc_info=True)
                    raise
            
            yield {"type": "model", "data": {"provider": provider, "name": model or "default"}}
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield {"type": "error", "data": f"Generation error: {str(e)}"}
            
    finally:
        # Clean up memory to prevent leaks
        # Clear large data structures that accumulate during processing
        if citations:
            citations.clear()
        if queries:
            queries.clear()
        if chunks_for_rerank:
            chunks_for_rerank.clear()
        if messages:
            messages.clear()
        if context_parts:
            context_parts.clear()
        
        # Clear string references
        context = ""
        
        logger.debug("Streaming pipeline cleanup completed")
