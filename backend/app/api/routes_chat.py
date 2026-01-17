"""
Chat API routes.
Handles RAG-based question answering with LLM provider selection.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import ChatAudit
from app.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.rag.graph import run_rag_pipeline
from app.core.logging import get_logger

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process a chat question using RAG pipeline.
    
    Flow:
    1. Validate provider and model
    2. Retrieve relevant chunks from Pinecone (filtered by doc_ids if provided)
    3. Build prompt with context
    4. Call selected LLM (Ollama/OpenAI/Anthropic)
    5. Return answer with citations
    6. Log to audit table
    
    Args:
        request: ChatRequest with question, provider, optional filters
        db: Database session
    
    Returns:
        ChatResponse with answer, citations, and model info
    """
    try:
        # Validate provider
        valid_providers = ["ollama", "openai", "anthropic"]
        if request.provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
            )
        
        logger.info(f"Processing chat request from user {request.user_id} with provider {request.provider}")
        
        # Run RAG pipeline
        try:
            result = run_rag_pipeline(
                question=request.question,
                provider=request.provider,
                model=request.model,
                doc_ids=request.doc_ids,
                top_k=request.top_k or 5
            )
        except ValueError as e:
            # Handle configuration errors (missing API keys, etc.)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing question: {str(e)}"
            )
        
        # Extract cited document IDs
        cited_doc_ids = list(set([
            citation["doc_id"] for citation in result["citations"]
        ]))
        
        # Save to audit log
        try:
            audit = ChatAudit(
                user_id=request.user_id,
                provider=request.provider,
                model=request.model or result["model"]["name"],
                question=request.question,
                answer=result["answer"],
                cited_doc_ids=cited_doc_ids if cited_doc_ids else None
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Error saving chat audit: {e}")
        
        logger.info(f"Chat request completed successfully with {len(result['citations'])} citations")
        
        return ChatResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
