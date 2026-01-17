"""
Production RAG Server - Phase 2
Full-featured RAG backend with:
- ChromaDB vector store for semantic search
- SQLite database for persistence
- Real document embedding and retrieval
- Multi-provider LLM support (Ollama, OpenAI, Anthropic)
- Conversation memory with database persistence

Run with: python production_server.py
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Dict, Any
import os
import requests
import json
from datetime import datetime
from pathlib import Path
import uuid

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded environment from {env_path}")
    else:
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[OK] Loaded environment from {env_path}")
except ImportError:
    print("[WARNING] python-dotenv not installed")

# Import our modules
try:
    from app.rag.vector_store import get_vector_store, VectorStore
    from app.rag.retriever import get_retriever, RAGRetriever
    from app.rag.chunking import chunk_document
    from app.db.database import get_database, DatabaseManager
    RAG_AVAILABLE = True
    print("[OK] RAG modules loaded")
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"[WARNING] RAG modules not available: {e}")
    print("[INFO] Install with: pip install -r requirements-phase2.txt")

# Initialize FastAPI
app = FastAPI(
    title="Policy RAG API - Production",
    description="Production-ready RAG API with semantic search and persistence",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Initialize services (lazy loading)
_retriever: Optional[RAGRetriever] = None
_db: Optional[DatabaseManager] = None


def get_services():
    """Get or initialize services."""
    global _retriever, _db
    
    if RAG_AVAILABLE:
        if _retriever is None:
            _retriever = get_retriever(persist_directory=str(DATA_DIR / "chroma_db"))
        if _db is None:
            _db = get_database(f"sqlite:///{DATA_DIR}/policy_rag.db")
    
    return _retriever, _db


# Pydantic models
class ChatRequest(BaseModel):
    question: str
    provider: str = "ollama"
    model: Optional[str] = None
    user_id: str = "default-user"
    doc_ids: List[str] = []


class ChatResponse(BaseModel):
    answer: str
    citations: List[dict] = []
    model: Optional[dict] = None
    context_used: bool = False


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    preview_text: str
    size: int
    is_indexed: bool = False
    chunk_count: int = 0


# LLM calling functions
def call_ollama(model: str, messages: List[dict], context: str = "") -> Optional[str]:
    """Call Ollama API."""
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        print(f"[ERROR] Ollama error: {response.status_code}")
        return None
    except Exception as e:
        print(f"[ERROR] Ollama error: {e}")
        return None


def call_openai(model: str, messages: List[dict], api_key: str) -> Optional[str]:
    """Call OpenAI API."""
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1500
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"[ERROR] OpenAI error: {e}")
        return None


def call_anthropic(model: str, messages: List[dict], api_key: str) -> Optional[str]:
    """Call Anthropic API."""
    try:
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "system": system_msg,
                "messages": user_messages,
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        return None
    except Exception as e:
        print(f"[ERROR] Anthropic error: {e}")
        return None


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    retriever, db = get_services()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "Policy RAG API - Production",
        "features": {
            "rag_enabled": RAG_AVAILABLE,
            "vector_store": retriever is not None,
            "database": db is not None
        }
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Policy RAG API - Production",
        "version": "2.0.0",
        "description": "Production RAG API with semantic search",
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "upload": "/api/docs/upload",
            "chat": "/api/chat",
            "stats": "/api/stats"
        }
    }


@app.get("/api/docs")
async def list_documents():
    """List all documents."""
    retriever, db = get_services()
    
    if db:
        docs = db.get_all_documents()
        return {"documents": [doc.to_dict() for doc in docs]}
    
    # Fallback: return empty list
    return {"documents": []}


@app.post("/api/docs/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and index a document."""
    retriever, db = get_services()
    
    # Read file content
    content = await file.read()
    text_content = content.decode('utf-8', errors='ignore')
    
    # Generate document ID
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    
    # Save to database
    if db:
        doc = db.create_document(
            doc_id=doc_id,
            filename=file.filename,
            content=text_content,
            content_type=file.content_type or "text/plain"
        )
        print(f"[OK] Document saved to database: {file.filename}")
    
    # Index in vector store (in background for large files)
    if retriever and len(text_content) > 0:
        # Index document
        chunk_count = retriever.index_document(
            doc_id=doc_id,
            content=text_content,
            filename=file.filename
        )
        
        # Update database with index status
        if db:
            db.update_document_indexed(doc_id, chunk_count)
        
        print(f"[OK] Document indexed: {file.filename} ({chunk_count} chunks)")
    
    return {
        "success": True,
        "id": doc_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "preview_text": text_content[:200],
        "size": len(content),
        "is_indexed": retriever is not None
    }


@app.delete("/api/docs/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    retriever, db = get_services()
    
    # Delete from vector store
    if retriever:
        retriever.delete_document(doc_id)
    
    # Delete from database
    if db:
        db.delete_document(doc_id)
    
    return {"success": True, "message": f"Document {doc_id} deleted"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with RAG."""
    retriever, db = get_services()
    
    # Build context from retrieved documents
    context = ""
    citations = []
    context_used = False
    
    if retriever and RAG_AVAILABLE:
        # Get relevant context
        filter_ids = request.doc_ids if request.doc_ids else None
        context_data = retriever.build_context(
            query=request.question,
            n_results=5,
            filter_doc_ids=filter_ids,
            max_context_length=3000
        )
        
        if context_data["num_chunks"] > 0:
            context = context_data["context"]
            citations = context_data["citations"]
            context_used = True
            print(f"[INFO] Retrieved {context_data['num_chunks']} relevant chunks")
    
    # Build system prompt
    if context:
        system_prompt = f"""You are a helpful AI assistant for company policy questions. 
Use the following document excerpts to answer the user's question accurately.
Always cite your sources when providing information.
If the context doesn't contain relevant information, say so and provide general guidance.

RELEVANT DOCUMENT EXCERPTS:
{context}

INSTRUCTIONS:
- Answer based on the provided context
- Be specific and cite which document the information comes from
- If information is not in the context, clearly state that
- Be helpful and professional"""
    else:
        system_prompt = """You are a helpful AI assistant for company policy questions.
You help users understand company policies on topics like:
- Leave policies (annual, sick, parental)
- Remote work and hybrid arrangements
- Data privacy and security
- Non-disclosure agreements
- Expense reimbursement

Please provide helpful, accurate information. If you don't have specific policy details, 
provide general guidance and suggest the user check with HR."""
    
    # Get conversation history from database
    history_messages = []
    if db:
        history = db.get_chat_history(request.user_id, limit=6)
        for msg in history:
            history_messages.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": request.question})
    
    # Call LLM
    answer = None
    actual_model = None
    
    if request.provider == "ollama":
        actual_model = request.model or "llama3.1:8b"
        answer = call_ollama(actual_model, messages, context)
    
    elif request.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            actual_model = request.model or "gpt-4o-mini"
            answer = call_openai(actual_model, messages, api_key)
        else:
            answer = "⚠️ OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            actual_model = request.model or "gpt-4o-mini"
    
    elif request.provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            actual_model = request.model or "claude-3-sonnet-20240229"
            answer = call_anthropic(actual_model, messages, api_key)
        else:
            answer = "⚠️ Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
            actual_model = request.model or "claude-3-sonnet-20240229"
    
    # Fallback response
    if not answer:
        if context_used:
            answer = f"""Based on the retrieved documents, here's what I found relevant to your question:

{context[:1500]}...

For a more detailed AI-generated answer, please ensure Ollama is running (ollama serve) 
or configure OpenAI/Anthropic API keys."""
        else:
            answer = """I'm currently running in limited mode. To get full AI-powered answers:

**For Ollama (Free, Local):**
- Install Ollama from https://ollama.ai
- Run: `ollama serve` and `ollama pull llama3.1`

**For OpenAI (Paid):**
- Set OPENAI_API_KEY environment variable

**For Anthropic (Paid):**
- Set ANTHROPIC_API_KEY environment variable

In the meantime, try uploading some documents and I can search through them for relevant information."""
    
    # Save to database
    if db:
        # Save user message
        db.save_chat_message(
            user_id=request.user_id,
            role="user",
            content=request.question
        )
        
        # Save assistant message with citations
        db.save_chat_message(
            user_id=request.user_id,
            role="assistant",
            content=answer,
            provider=request.provider,
            model=actual_model,
            citations=citations
        )
    
    return ChatResponse(
        answer=answer,
        citations=citations,
        model={"provider": request.provider, "name": actual_model},
        context_used=context_used
    )


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    retriever, db = get_services()
    
    stats = {
        "rag_available": RAG_AVAILABLE,
        "vector_store": {},
        "database": {}
    }
    
    if retriever:
        stats["vector_store"] = retriever.get_stats()
    
    if db:
        stats["database"] = db.get_stats()
    
    return stats


@app.post("/api/chat/clear")
async def clear_chat_history(user_id: str = "default-user"):
    """Clear chat history for a user."""
    retriever, db = get_services()
    
    if db:
        count = db.clear_chat_history(user_id)
        return {"success": True, "messages_cleared": count}
    
    return {"success": False, "message": "Database not available"}


@app.get("/api/chat/history")
async def get_chat_history(user_id: str = "default-user", limit: int = 20):
    """Get chat history for a user."""
    retriever, db = get_services()
    
    if db:
        history = db.get_chat_history(user_id, limit)
        return {
            "user_id": user_id,
            "messages": [msg.to_dict() for msg in history]
        }
    
    return {"user_id": user_id, "messages": []}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("\n" + "="*70)
    print("  POLICY RAG API - Production Server (Phase 2)")
    print("="*70)
    
    # Initialize services
    retriever, db = get_services()
    
    if retriever:
        stats = retriever.get_stats()
        print(f"\n[OK] Vector Store: {stats['total_chunks']} chunks from {stats['unique_documents']} documents")
    
    if db:
        stats = db.get_stats()
        print(f"[OK] Database: {stats['total_documents']} documents, {stats['total_messages']} messages")
    
    print(f"\n[INFO] Data directory: {DATA_DIR}")
    print("\nAccess points:")
    print("  - API:  http://localhost:8001")
    print("  - Docs: http://localhost:8001/docs")
    print("  - Stats: http://localhost:8001/api/stats")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
