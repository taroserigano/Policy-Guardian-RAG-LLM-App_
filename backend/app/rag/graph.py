"""
LangGraph-based RAG workflow.
Orchestrates retrieval and generation with proper state management.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from app.core.logging import get_logger
from app.rag.retrieval import retrieve_relevant_chunks, Citation
from app.rag.llms import get_llm

logger = get_logger(__name__)


class RAGState(TypedDict):
    """State for RAG workflow."""
    question: str
    provider: str
    model: Optional[str]
    doc_ids: Optional[List[str]]
    top_k: int
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
        system_prompt = """You are a helpful AI assistant specializing in policy, compliance, and legal document analysis.

Your role is to:
1. Answer questions ONLY based on the provided context from official documents
2. Be precise and cite specific sources when possible
3. If the information is not in the context, clearly state that you don't have that information
4. Use professional, clear language appropriate for legal/compliance contexts
5. Never make assumptions or provide information not present in the context

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
