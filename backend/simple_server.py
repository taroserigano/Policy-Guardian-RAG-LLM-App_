"""
Simplified backend server that bypasses dependency conflicts.
Run with: python simple_server.py
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Dict
import os
import requests
import json
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from parent directory (.env is in project root, not backend/)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    print(f"[OK] Loaded environment variables from {env_path}")
except ImportError:
    print("[WARNING] python-dotenv not installed. Install with: pip install python-dotenv")
    print("[WARNING] Falling back to system environment variables")

app = FastAPI(title="Policy RAG API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage with pre-loaded sample documents
documents = [
    {
        "id": "doc-1",
        "filename": "employee_leave_policy.txt",
        "content_type": "text/plain",
        "preview_text": "EMPLOYEE LEAVE POLICY - Annual Leave: 20 days per year, Sick Leave: 10 days, Parental Leave: up to 16 weeks (primary caregiver)...",
        "size": 3500
    },
    {
        "id": "doc-2",
        "filename": "remote_work_policy.txt",
        "content_type": "text/plain",
        "preview_text": "REMOTE WORK POLICY - Hybrid: 2 days remote per week, Full Remote: 3+ days requires approval, Core hours 9-4 PM...",
        "size": 4200
    },
    {
        "id": "doc-3",
        "filename": "data_privacy_policy.txt",
        "content_type": "text/plain",
        "preview_text": "DATA PRIVACY POLICY - Cross-jurisdiction privacy principles, retention schedule, security controls, incident handling...",
        "size": 5800
    },
    {
        "id": "doc-4",
        "filename": "non_disclosure_agreement.txt",
        "content_type": "text/plain",
        "preview_text": "NON-DISCLOSURE AGREEMENT - Confidential information protection, 3 year term, 5 year confidentiality obligation...",
        "size": 3200
    }
]
# Conversation memory: {user_id: [{role: str, content: str, timestamp: str}]}
conversation_history: Dict[str, List[dict]] = {}

class ChatRequest(BaseModel):
    question: str
    provider: str = "ollama"
    model: Optional[str] = None  # Model name is optional, will use provider default if not specified
    user_id: str
    doc_ids: List[str] = []

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict] = []
    model: Optional[dict] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0", "service": "Policy RAG API - Simple Server"}

@app.get("/")
async def root():
    return {
        "name": "Policy RAG API - Simple Server",
        "version": "1.0.0",
        "description": "Simplified RAG API for demo purposes"
    }

@app.post("/api/docs/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document."""
    content = await file.read()
    
    doc = {
        "id": f"doc-{len(documents) + 1}",
        "filename": file.filename,
        "content_type": file.content_type,
        "preview_text": content[:200].decode('utf-8', errors='ignore'),
        "size": len(content)
    }
    documents.append(doc)
    
    return {"success": True, **doc}

@app.get("/api/docs")
async def list_documents():
    """List all documents."""
    return {"documents": documents}

def call_ollama(model: str, messages: List[dict], context: str) -> str:
    """Call Ollama API for chat completion."""
    try:
        print(f"[DEBUG] Calling Ollama with model: {model}")
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=60
        )
        print(f"[DEBUG] Ollama response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()["message"]["content"]
            print(f"[DEBUG] Ollama result: {result[:100]}...")
            return result
        print(f"[DEBUG] Ollama error: {response.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Ollama error: {e}")
        return None

def call_openai(model: str, messages: List[dict], api_key: str) -> str:
    """Call OpenAI API for chat completion."""
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
                "max_tokens": 1000
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None

def call_anthropic(model: str, messages: List[dict], api_key: str) -> str:
    """Call Anthropic API for chat completion."""
    try:
        print(f"[DEBUG] Calling Anthropic with model: {model}")
        # Convert messages format for Anthropic
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
                "max_tokens": 1000,
                "temperature": 0.7
            },
            timeout=60
        )
        print(f"[DEBUG] Anthropic response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()["content"][0]["text"]
            print(f"[DEBUG] Anthropic result: {result[:100]}...")
            return result
        else:
            print(f"[DEBUG] Anthropic error response: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Anthropic error: {e}")
        return None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with real LLM calls and conversation memory."""
    
    # Get conversation history for this user
    if request.user_id not in conversation_history:
        conversation_history[request.user_id] = []
    
    user_history = conversation_history[request.user_id]
    
    # Build document context
    context = """You are a helpful AI assistant for company policy questions. Use the following document excerpts to answer questions:

**EMPLOYEE LEAVE POLICY:**
- Annual Leave: 20 days paid per year for full-time employees (1.67 days/month accrual)
- Sick Leave: 10 days paid per year (medical cert required >3 days)
- Maternity: 16 weeks (8 weeks 100% pay, 8 unpaid)
- Paternity: 2 weeks paid
- Compassionate: 5 days paid (immediate family), 2 days (extended family)
- Request process: HR portal, 2 weeks advance notice, manager approval required

**REMOTE WORK POLICY:**
- Hybrid: Up to 2 days/week remote with manager approval
- Full Remote: 3+ days/week requires department head approval
- Equipment: Laptop, monitor, peripherals, $500 home office stipend, $75/month internet
- Requirements: 6 months service, reliable 25 Mbps internet, appropriate workspace

**DATA PRIVACY POLICY:**
- Retention: Employee (7 years), Customer (7 years), Financial (7 years)
- Security: TLS 1.2+, AES-256 encryption, MFA required
- Rights: Data access, rectification, erasure, portability
- Breach notification: Within 72 hours
- GDPR/CCPA compliant

**NON-DISCLOSURE AGREEMENT:**
- Covers: Technical designs, business plans, trade secrets, employee records
- Duration: 3 year agreement, 5 year confidentiality obligation
- Obligations: Strict confidence, reasonable care, no unauthorized disclosure
- Trade secrets: Confidential indefinitely

Answer based on this context and previous conversation."""
    
    # Build messages with conversation history
    messages = [{"role": "system", "content": context}]
    
    # Add recent history (last 6 messages = 3 exchanges)
    recent_history = user_history[-6:] if len(user_history) > 6 else user_history
    for msg in recent_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current question
    messages.append({"role": "user", "content": request.question})
    
    # Try to call the selected LLM
    answer = None
    actual_model = None  # Track which model was actually used
    
    if request.provider == "ollama":
        # Default to fine-tuned model for policy questions, fallback to base model
        actual_model = request.model or "policy-compliance-llm"
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
            actual_model = request.model or "claude-3-sonnet-20240229"  # Use stable Claude 3 Sonnet
            answer = call_anthropic(actual_model, messages, api_key)
        else:
            answer = "⚠️ Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
            actual_model = request.model or "claude-3-sonnet-20240229"
    
    # Fallback to mock response if LLM fails
    if not answer:
        answer = """I'm currently running in demo mode. To use real AI responses:
        
**For Ollama (Free, Local):**
- Install Ollama from https://ollama.ai
- Run: `ollama pull llama3.1`
- Make sure Ollama is running on http://localhost:11434

**For OpenAI (Paid):**
- Set OPENAI_API_KEY environment variable
- Uses gpt-4o-mini model

**For Anthropic (Paid):**
- Set ANTHROPIC_API_KEY environment variable  
- Uses claude-3-5-sonnet model

Based on your question about company policies, here's what I can tell you from our documents:

📋 **Leave Policies:** 20 days annual, 10 sick, 16 weeks maternity, 2 weeks paternity
🏠 **Remote Work:** 2 days/week hybrid, full remote needs approval
🔒 **Data Privacy:** 7-year retention, GDPR compliant, 72hr breach notification
📝 **NDA:** 3-year term, 5-year confidentiality obligation

Ask specific questions for detailed information!"""
    
    # Store conversation in history
    user_history.append({
        "role": "user",
        "content": request.question,
        "timestamp": datetime.now().isoformat()
    })
    user_history.append({
        "role": "assistant",
        "content": answer,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 20 messages (10 exchanges)
    if len(user_history) > 20:
        conversation_history[request.user_id] = user_history[-20:]
    
    # Build citations based on question keywords
    relevant_docs = []
    question_lower = request.question.lower()
    if any(word in question_lower for word in ["leave", "vacation", "sick", "maternity", "paternity", "time off", "annual"]):
        relevant_docs.append("doc-1")
    if any(word in question_lower for word in ["remote", "work from home", "wfh", "hybrid", "equipment"]):
        relevant_docs.append("doc-2")
    if any(word in question_lower for word in ["privacy", "data", "gdpr", "retention", "security", "breach"]):
        relevant_docs.append("doc-3")
    if any(word in question_lower for word in ["nda", "confidential", "disclosure", "secret", "proprietary"]):
        relevant_docs.append("doc-4")
    
    # If no specific keywords, return all docs
    if not relevant_docs:
        relevant_docs = ["doc-1", "doc-2", "doc-3", "doc-4"]
    
    # Build citations from relevant documents
    citations = []
    for doc_id in relevant_docs:
        doc = next((d for d in documents if d["id"] == doc_id), None)
        if doc:
            citations.append({
                "doc_id": doc["id"],
                "filename": doc["filename"],
                "chunk_index": 0,
                "score": 0.92,
                "text": doc["preview_text"]
            })
    
    # Add model information
    model_info = {
        "provider": request.provider,
        "name": actual_model or request.model
    }
    
    return ChatResponse(answer=answer, citations=citations, model=model_info)

if __name__ == "__main__":
    print("="*70)
    print("  POLICY RAG API - Enhanced Server with LLM Integration")
    print("="*70)
    print("\n[START] Starting server...")
    print("[INFO] Features: Real LLM calls + Conversation Memory")
    print("       Supports: Ollama (local), OpenAI, Anthropic\n")
    print("Access points:")
    print("  - API:  http://localhost:8001")
    print("  - Docs: http://localhost:8001/docs")
    print("  - Frontend: http://localhost:5173\n")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
