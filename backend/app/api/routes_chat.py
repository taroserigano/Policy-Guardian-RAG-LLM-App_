"""
Chat API routes.
Handles RAG-based question answering with LLM provider selection.
Supports both regular and streaming responses.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from app.db.session import get_db
from app.db.models import ChatAudit, ImageDocument
from app.schemas import ChatRequest, ChatResponse, ChatHistoryResponse, ErrorResponse
from app.rag.graph import run_rag_pipeline, run_rag_pipeline_streaming
from app.rag.multimodal_retrieval import retrieve_multimodal
from app.rag.llms import get_streaming_llm
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
            if db is not None:
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
            else:
                logger.warning("Database not available, skipping audit log")
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


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Stream chat response using Server-Sent Events (SSE).
    
    Returns tokens as they are generated, followed by citations at the end.
    
    Event types:
    - token: A text chunk from the LLM
    - citations: Array of citation objects (sent once at end)
    - done: Signals completion
    - error: Error message if something went wrong
    """
    # Validate provider upfront
    valid_providers = ["ollama", "openai", "anthropic"]
    if request.provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
        )
    
    logger.info(f"Processing streaming chat request from user {request.user_id}")
    
    # Check if multimodal mode (images selected)
    is_multimodal = request.image_ids and len(request.image_ids) > 0
    
    # Extract RAG options
    rag_options = None
    if request.rag_options:
        rag_options = {
            'query_expansion': request.rag_options.query_expansion,
            'hybrid_search': request.rag_options.hybrid_search,
            'reranking': request.rag_options.reranking
        }
        logger.info(f"RAG options: {rag_options}")
    
    # Store request data for use in generator (db session will be closed after this function returns)
    request_data = {
        "user_id": request.user_id,
        "provider": request.provider,
        "model": request.model,
        "question": request.question,
        "image_ids": request.image_ids if is_multimodal else None,
        "doc_ids": request.doc_ids,
        "top_k": request.top_k or 5,
        "is_multimodal": is_multimodal
    }
    
    def generate():
        full_answer = ""
        citations = []
        model_info = {"provider": request_data["provider"], "name": request_data["model"] or "default"}
        image_details = []
        image_data_for_vision = []
        
        try:
            # LAZY LOAD: Load image data only when streaming starts
            if request_data["is_multimodal"] and request_data["image_ids"]:
                logger.info(f"Loading {len(request_data['image_ids'])} images for multimodal chat")
                try:
                    from app.db.session import get_db_context
                    with get_db_context() as img_db:
                        if img_db:
                            images = img_db.query(ImageDocument).filter(
                                ImageDocument.id.in_(request_data["image_ids"])
                            ).all()
                            logger.info(f"Found {len(images)} images in database")
                            
                            for img in images:
                                desc = img.description or img.extracted_text or "No description available"
                                image_details.append({
                                    "id": img.id,
                                    "filename": img.filename,
                                    "description": desc,
                                    "thumbnail_base64": img.thumbnail_base64,
                                    "content_type": img.content_type
                                })
                                
                                # Store actual image data for vision model analysis
                                if img.image_base64:
                                    image_data_for_vision.append({
                                        "id": img.id,
                                        "filename": img.filename,
                                        "image_base64": img.image_base64,
                                        "content_type": img.content_type
                                    })
                                    logger.debug(f"Image {img.filename}: using full image data")
                                elif img.thumbnail_base64:
                                    image_data_for_vision.append({
                                        "id": img.id,
                                        "filename": img.filename,
                                        "image_base64": img.thumbnail_base64,
                                        "content_type": "image/png"
                                    })
                                    logger.debug(f"Image {img.filename}: using thumbnail")
                except Exception as e:
                    logger.error(f"Error loading image data: {e}")
            
            # If images are selected, use image-focused chat with vision model
            if request_data["is_multimodal"] and image_details:
                logger.info(f"Running image-focused chat with {len(image_details)} images")
                
                # Check if we have actual image data for vision analysis
                if image_data_for_vision:
                    logger.info(f"Using vision model for {len(image_data_for_vision)} images with actual image data")
                    
                    # Get document context if doc_ids provided
                    doc_context = ""
                    if request_data["doc_ids"]:
                        try:
                            from app.rag.retrieval import retrieve_relevant_chunks
                            # retrieve_relevant_chunks returns (List[Citation], context_str)
                            citation_objs, doc_context = retrieve_relevant_chunks(
                                query=request_data["question"],
                                top_k=request_data["top_k"],
                                doc_ids=request_data["doc_ids"]
                            )
                            if citation_objs:
                                citations = [c.to_dict() for c in citation_objs]
                                logger.info(f"Retrieved {len(citation_objs)} document chunks for vision context")
                        except Exception as e:
                            logger.error(f"Error retrieving document context: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                    
                    # Use vision model for real image analysis
                    from app.rag.vision_models import get_vision_model
                    import base64
                    
                    # Build the prompt with context - include eligibility category
                    if doc_context:
                        vision_prompt = f"""You are an AI assistant analyzing images in the context of policy documents.

=== RELEVANT POLICY DOCUMENTS ===
{doc_context}

=== USER QUESTION ===
{request_data['question']}

IMPORTANT: Start your response with EXACTLY this format on the first line:
**Eligibility Score: XX/100 - [CATEGORY]**

Where [CATEGORY] is one of:
- "Approved" (80-100)
- "Likely Eligible" (60-79)  
- "Needs Review" (40-59)
- "Unlikely" (20-39)
- "Not Eligible" (0-19)

Then give a BRIEF explanation (3-4 sentences max) of why, citing the key policy criteria met or not met. Be concise. DO NOT repeat the score or category."""
                    else:
                        vision_prompt = f"""You are an AI assistant helping analyze images.

=== USER QUESTION ===
{request_data['question']}

Provide a brief, helpful answer (3-4 sentences max)."""
                    
                    # Use the first image for vision analysis (for now, supporting single image)
                    img_data = image_data_for_vision[0]
                    image_bytes = base64.b64decode(img_data["image_base64"])
                    
                    # Get vision model based on provider
                    vision_provider = request_data["provider"]
                    
                    # For Ollama, check if LLaVA is available, otherwise fallback to OpenAI
                    if vision_provider == "ollama":
                        try:
                            import httpx
                            ollama_url = "http://localhost:11434"
                            resp = httpx.get(f"{ollama_url}/api/tags", timeout=3.0)
                            if resp.status_code == 200:
                                models = resp.json().get("models", [])
                                has_llava = any("llava" in m.get("name", "").lower() for m in models)
                                if has_llava:
                                    logger.info("Using Ollama LLaVA for vision analysis")
                                else:
                                    vision_provider = "openai"
                                    logger.info("LLaVA not found in Ollama, falling back to OpenAI vision")
                            else:
                                vision_provider = "openai"
                                logger.info("Ollama not responding, falling back to OpenAI vision")
                        except Exception as e:
                            vision_provider = "openai"
                            logger.info(f"Ollama check failed ({e}), falling back to OpenAI vision")
                    
                    vision_model = get_vision_model(vision_provider)
                    
                    # Analyze image with vision model
                    logger.info(f"Analyzing image with {vision_provider} vision model...")
                    analysis = vision_model.analyze_image(image_bytes, vision_prompt, max_tokens=500)
                    
                    # Stream the response
                    model_info = {"provider": vision_provider, "name": f"{vision_provider}-vision"}
                    
                    # Send the analysis in chunks to simulate streaming
                    chunk_size = 20
                    for i in range(0, len(analysis), chunk_size):
                        chunk = analysis[i:i + chunk_size]
                        full_answer += chunk
                        yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"
                    
                    # Send citations if we have document context
                    yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"
                
                else:
                    # No image data for vision - use description-based fallback
                    logger.info("Using description-based analysis (no image data for vision)")
                    
                    # Check if any images lack descriptions - they need to be re-uploaded
                    images_without_data = [img for img in image_details if not img['description'] or img['description'] == "No description available"]
                    if images_without_data:
                        missing_names = [img['filename'] for img in images_without_data]
                        logger.warning(f"Images without description or image data: {missing_names}")
                    
                    # Get document context if doc_ids provided
                    doc_context = ""
                    if request_data["doc_ids"]:
                        try:
                            from app.rag.retrieval import retrieve_relevant_chunks
                            # retrieve_relevant_chunks returns (List[Citation], context_str)
                            citation_objs, doc_context = retrieve_relevant_chunks(
                                query=request_data["question"],
                                top_k=request_data["top_k"],
                                doc_ids=request_data["doc_ids"]
                            )
                            if citation_objs:
                                citations = [c.to_dict() for c in citation_objs]
                                logger.info(f"Retrieved {len(citation_objs)} document chunks for fallback context")
                        except Exception as e:
                            logger.error(f"Error retrieving document context: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                    
                    # Build system prompt for image analysis
                    if doc_context:
                        system_prompt = """You are an AI assistant that helps users understand images in the context of policy documents.
You have been provided with descriptions of images and relevant policy documents.
Answer the user's question based on both the image descriptions and the policy documents.
If the question is about eligibility or compliance, compare the image details against the policy requirements.
If an image has no description, explain that it was uploaded before vision analysis was enabled and needs to be re-uploaded for proper analysis."""
                    else:
                        system_prompt = """You are an AI assistant that helps users understand images. 
You have been provided with descriptions of images that the user wants to ask about.
Answer the user's question based on the image descriptions provided.
Be specific and reference the image details when answering.
If an image has no description, explain that it was uploaded before vision analysis was enabled and needs to be re-uploaded with 'Auto AI Description' enabled for proper analysis."""

                    # Build image context
                    image_context_parts = ["=== IMAGE DESCRIPTIONS ==="]
                    for img in image_details:
                        image_context_parts.append(f"\nImage: {img['filename']}")
                        image_context_parts.append(f"Description: {img['description']}")
                    image_context = "\n".join(image_context_parts)
                    
                    # Build full context with documents if available
                    if doc_context:
                        full_context = f"{image_context}\n\n=== RELEVANT POLICY DOCUMENTS ===\n{doc_context}\n\n=== USER QUESTION ===\n{request_data['question']}"
                    else:
                        full_context = f"{image_context}\n\n=== USER QUESTION ===\n{request_data['question']}"
                    
                    # Create messages for LLM
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_context}
                    ]
                    
                    # Get streaming LLM and generate response
                    llm = get_streaming_llm(request_data["provider"], request_data["model"])
                    model_info = {"provider": request_data["provider"], "name": request_data["model"] or llm.model if hasattr(llm, 'model') else "default"}
                    
                    for token in llm.stream(messages):
                        if hasattr(token, 'content'):
                            token_text = token.content
                        else:
                            token_text = str(token)
                        full_answer += token_text
                        yield f"data: {json.dumps({'type': 'token', 'data': token_text})}\n\n"
                    
                    # Send citations (from document sources if any)
                    yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"
                
            else:
                # Normal document RAG flow
                for event in run_rag_pipeline_streaming(
                    question=request_data["question"],
                    provider=request_data["provider"],
                    model=request_data["model"],
                    doc_ids=request_data["doc_ids"],
                    top_k=request_data["top_k"],
                    rag_options=rag_options
                ):
                    if event["type"] == "token":
                        full_answer += event["data"]
                        yield f"data: {json.dumps({'type': 'token', 'data': event['data']})}\n\n"
                    elif event["type"] == "citations":
                        citations = event["data"]
                        yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"
                    elif event["type"] == "model":
                        model_info = event["data"]
                    elif event["type"] == "error":
                        yield f"data: {json.dumps({'type': 'error', 'data': event['data']})}\n\n"
                        return
            
            # Send images info if multimodal
            if request_data["is_multimodal"] and image_details:
                yield f"data: {json.dumps({'type': 'images', 'data': image_details})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'data': {'model': model_info}})}\n\n"
            
            # Save to audit log with a NEW database session
            # (original session is closed after the route function returns)
            try:
                from app.db.session import get_db_context
                with get_db_context() as audit_db:
                    if audit_db:
                        cited_doc_ids = list(set([c["doc_id"] for c in citations])) if citations else []
                        cited_image_ids = request_data["image_ids"]
                        audit = ChatAudit(
                            user_id=request_data["user_id"],
                            provider=request_data["provider"],
                            model=request_data["model"] or model_info["name"],
                            question=request_data["question"],
                            answer=full_answer,
                            cited_doc_ids=cited_doc_ids if cited_doc_ids else None,
                            cited_image_ids=cited_image_ids
                        )
                        audit_db.add(audit)
                        audit_db.commit()
                        logger.debug("Chat audit saved successfully")
            except Exception as e:
                logger.error(f"Error saving chat audit: {e}")
                
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        finally:
            # MEMORY CLEANUP: Clear large data structures
            if 'full_answer' in locals():
                full_answer = ""
            if 'citations' in locals():
                citations.clear()
            if 'image_details' in locals():
                image_details.clear()
            if 'image_data_for_vision' in locals():
                image_data_for_vision.clear()
            logger.debug("Streaming generator cleanup completed")
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/history/{user_id}", response_model=List[ChatHistoryResponse])
def get_chat_history(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a specific user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of messages to return (default 50)
    
    Returns:
        List of chat history entries ordered by most recent first
    """
    try:
        if db is None:
            logger.warning("Database not available, returning empty chat history")
            return []
            
        history = db.query(ChatAudit)\
            .filter(ChatAudit.user_id == user_id)\
            .order_by(ChatAudit.created_at.desc())\
            .limit(limit)\
            .all()
        
        return history
    
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching chat history"
        )


@router.delete("/history/{user_id}")
def clear_chat_history(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear all chat history for a specific user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Number of entries deleted
    """
    try:
        if db is None:
            logger.warning("Database not available, cannot clear chat history")
            return {
                "message": "Database not available",
                "deleted_count": 0
            }
            
        deleted_count = db.query(ChatAudit)\
            .filter(ChatAudit.user_id == user_id)\
            .delete()
        db.commit()
        
        logger.info(f"Deleted {deleted_count} chat history entries for user {user_id}")
        
        return {
            "message": f"Deleted {deleted_count} chat history entries",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing chat history"
        )


@router.get("/history/{user_id}/export")
def export_chat_history(
    user_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Export chat history for a user in specified format.
    
    Args:
        user_id: User identifier
        format: Export format ('json' or 'markdown')
    
    Returns:
        File download with chat history
    """
    try:
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )
        
        # Get chat history
        history = db.query(ChatAudit)\
            .filter(ChatAudit.user_id == user_id)\
            .order_by(ChatAudit.created_at.asc())\
            .all()
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chat history found for this user"
            )
        
        # Format content based on requested format
        if format == "markdown":
            content = f"# Chat History - {user_id}\n\n"
            content += f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "---\n\n"
            
            for entry in history:
                timestamp = entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
                content += f"## {timestamp}\n\n"
                content += f"**User:** {entry.question}\n\n"
                content += f"**Assistant:** {entry.answer}\n\n"
                
                if entry.context_docs:
                    content += f"**Sources:** {', '.join(entry.context_docs)}\n\n"
                
                content += "---\n\n"
            
            media_type = "text/markdown"
            filename = f"chat_history_{user_id}_{datetime.now().strftime('%Y%m%d')}.md"
            
        else:  # json format
            history_data = []
            for entry in history:
                history_data.append({
                    "timestamp": entry.created_at.isoformat(),
                    "question": entry.question,
                    "answer": entry.answer,
                    "provider": entry.provider,
                    "model": entry.model,
                    "context_docs": entry.context_docs,
                    "context_images": entry.context_images
                })
            
            content = json.dumps(history_data, indent=2)
            media_type = "application/json"
            filename = f"chat_history_{user_id}_{datetime.now().strftime('%Y%m%d')}.json"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting chat history: {str(e)}"
        )
