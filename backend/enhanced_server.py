"""
Enhanced RAG Server - Phase 1 Complete
- PostgreSQL database persistence
- Pinecone vector store integration
- Proper document chunking with overlap
- Real semantic search
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI
import requests
import hashlib
import io

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Initialize components
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# OpenAI client for embeddings
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Models
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, index=True)
    content = Column(Text)
    content_hash = Column(String, unique=True, index=True)
    content_type = Column(String)
    size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatAudit(Base):
    __tablename__ = "chat_audit"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    model = Column(String)
    doc_ids = Column(String)  # JSON array as string
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "policy-rag")
pinecone_index = pc.Index(index_name)

app = FastAPI(title="Policy RAG API - Enhanced")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    question: str
    provider: str = "ollama"
    model: Optional[str] = None
    user_id: str
    doc_ids: List[str] = []

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict] = []
    model: Optional[dict] = None

def get_embedding(text: str) -> list:
    """Get embedding from OpenAI."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # 1536 dimensions
    )
    return response.data[0].embedding

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def extract_text_from_file(file_content: bytes, content_type: str, filename: str) -> str:
    """Extract text from uploaded file."""
    if content_type == "text/plain" or filename.endswith(".txt"):
        return file_content.decode("utf-8")
    elif content_type == "application/pdf" or filename.endswith(".pdf"):
        from pypdf import PdfReader
        pdf = PdfReader(io.BytesIO(file_content))
        return "\n\n".join(page.extract_text() for page in pdf.pages)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "features": ["database", "vector_store", "chunking"]}

@app.get("/")
async def root():
    return {"name": "Policy RAG API - Enhanced", "version": "2.0.0"}

@app.post("/api/docs/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index document."""
    db = SessionLocal()
    try:
        content_bytes = await file.read()
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        
        # Check if already exists
        existing = db.query(Document).filter(Document.content_hash == content_hash).first()
        if existing:
            return {"message": "Document already exists", "id": existing.id}
        
        # Extract text
        text = extract_text_from_file(content_bytes, file.content_type or "", file.filename or "")
        
        # Save to database
        doc = Document(
            filename=file.filename,
            content=text,
            content_hash=content_hash,
            content_type=file.content_type,
            size=len(content_bytes)
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Chunk and embed
        chunks = chunk_text(text)
        embeddings = embedding_model.encode(chunks).tolist()
        
        # Upload to Pinecone
        vectors = [
            {
                "id": f"{doc.id}-chunk-{i}",
                "values": emb,
                "metadata": {
                    "doc_id": doc.id,
                    "filename": file.filename,
                    "chunk_index": i,
                    "text": chunk[:500]  # Store first 500 chars
                }
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        pinecone_index.upsert(vectors=vectors)
        
        return {
            "message": "Document uploaded and indexed",
            "id": doc.id,
            "filename": file.filename,
            "chunks": len(chunks)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/docs")
async def list_documents():
    """List all documents."""
    db = SessionLocal()
    try:
        docs = db.query(Document).all()
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "size": doc.size,
                    "preview_text": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                }
                for doc in docs
            ]
        }
    finally:
        db.close()get_embedding(request.question

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with RAG."""
    db = SessionLocal()
    try:
        # Embed question
        question_embedding = embedding_model.encode([request.question])[0].tolist()
        
        # Search Pinecone
        filter_dict = {"doc_id": {"$in": [int(id) for id in request.doc_ids]}} if request.doc_ids else None
        results = pinecone_index.query(
            vector=question_embedding,
            top_k=5,
            include_metadata=True,
            filter=filter_dict
        )
        
        # Build context
        context_chunks = [match.metadata.get("text", "") for match in results.matches if match.score > 0.3]
        context = "\n\n".join(context_chunks)
        
        # Call LLM
        system_prompt = f"""You are a helpful assistant answering questions about company policies.
Use the following context to answer the question. If the answer is not in the context, say so.

Context:
{context}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.question}
        ]
        
        # Call provider
        if request.provider == "ollama":
            model = request.model or "llama3.1:8b"
            response = requests.post(
                f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat",
                json={"model": model, "messages": messages, "stream": False}
            )
            answer = response.json()["message"]["content"]
        else:
            answer = "Provider not implemented yet"
        
        # Save audit
        audit = ChatAudit(
            user_id=request.user_id,
            question=request.question,
            answer=answer,
            model=f"{request.provider}:{request.model or 'default'}",
            doc_ids=",".join(request.doc_ids)
        )
        db.add(audit)
        db.commit()
        
        # Build citations
        citations = [
            {
                "document": match.metadata.get("filename"),
                "chunk": match.metadata.get("chunk_index"),
                "score": round(match.score, 3),
                "text": match.metadata.get("text", "")[:200]
            }
            for match in results.matches if match.score > 0.3
        ]
        
        return ChatResponse(answer=answer, citations=citations, model={"provider": request.provider, "name": request.model})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 70)
    print("  POLICY RAG API - Enhanced (Phase 1)")
    print("=" * 70)
    print("\n[START] Starting enhanced server...")
    print("[INFO] Features:")
    print("       - PostgreSQL database persistence")
    print("       - Pinecone vector store")
    print("       - Semantic search with embeddings")
    print("       - Document chunking with overlap")
    print("\nAccess points:")
    print("  - API:  http://localhost:8001")
    print("  - Docs: http://localhost:8001/docs")
    print("  - Frontend: http://localhost:5173")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
