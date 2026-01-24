# Policy / Compliance / Legal RAG Application

A full-stack Retrieval-Augmented Generation (RAG) system for querying policy, compliance, and legal documents. Built with FastAPI, React, and supporting multiple LLM providers (Ollama, OpenAI, Anthropic).

## 🚀 Quick Start

**Windows:** Double-click `start.bat` in the project root  
**Manual Setup:** See [SETUP.md](SETUP.md) for detailed instructions

The app will open at `http://localhost:5173` with:

- ✅ Backend API on port 8001
- ✅ Frontend UI on port 5173
- ✅ Ollama LLM integration (if installed)

## 🌟 Features

- **Document Upload & Indexing**: Upload PDF and TXT documents with automatic text extraction, chunking, and vector embedding
- **Multi-Provider LLM Support**: Switch between Ollama (local), OpenAI GPT, and Anthropic Claude
- **Citation-Based Answers**: Every answer includes source citations with document name, page number, and chunk references
- **Document Filtering**: Select specific documents to narrow search scope
- **Audit Logging**: All Q&A interactions logged to PostgreSQL for compliance tracking
- **Modern UI**: Clean, responsive React interface with Tailwind CSS
- **Docker Support**: Complete containerization with Docker Compose

## 🏗️ Architecture

### Backend Stack

- **FastAPI**: High-performance Python web framework
- **LangGraph + LangChain**: RAG workflow orchestration
- **Pinecone**: Vector database for semantic search
- **PostgreSQL**: Relational database for metadata and audit logs
- **Ollama**: Local LLM inference (default)
- **OpenAI & Anthropic**: Cloud LLM alternatives

### Frontend Stack

- **React 18**: Modern UI library
- **Vite**: Fast build tool
- **React Router v6**: Client-side routing
- **React Query**: Data fetching and caching
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Icon library

### Training on Colab

<img width="1908" height="1076" alt="image" src="https://github.com/user-attachments/assets/d2683e9b-9aea-413b-a534-970cd54f7925" />


Loading Model

<img width="1916" height="1079" alt="image" src="https://github.com/user-attachments/assets/47504f9c-82d3-48be-a74e-78bcc8c734dc" />


Configure LoRA



<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/57104f1c-ea40-4e79-b899-86278a5cf3ca" />

Train and Merdge Adapter into Base Model 

<img width="1912" height="1079" alt="image" src="https://github.com/user-attachments/assets/d7668602-3d82-40d6-b982-a6d98cf64b7c" />

Fine Tuning locally on Adapter for merging 

<img width="1093" height="866" alt="image" src="https://github.com/user-attachments/assets/78a10850-d9cf-4601-ab08-f5b056a2c10f" />


### Project Structure

```
AI Rag 222/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Settings management
│   │   │   └── logging.py         # Logging configuration
│   │   ├── db/
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── session.py         # Database session
│   │   │   └── migrations.py      # DB initialization
│   │   ├── api/
│   │   │   ├── routes_docs.py     # Document endpoints
│   │   │   └── routes_chat.py     # Chat endpoints
│   │   ├── rag/
│   │   │   ├── embeddings.py      # Embedding generation
│   │   │   ├── llms.py            # LLM providers
│   │   │   ├── indexing.py        # Document indexing pipeline
│   │   │   ├── retrieval.py       # Vector search
│   │   │   └── graph.py           # LangGraph RAG workflow
│   │   ├── schemas.py             # Pydantic schemas
│   │   └── main.py                # FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js          # API client
│   │   ├── components/
│   │   │   ├── Layout.jsx
│   │   │   ├── FileDrop.jsx
│   │   │   ├── ModelPicker.jsx
│   │   │   ├── MessageList.jsx
│   │   │   ├── CitationsList.jsx
│   │   │   ├── ChatBox.jsx
│   │   │   └── DocumentList.jsx
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   └── ChatPage.jsx
│   │   ├── hooks/
│   │   │   └── useApi.js          # React Query hooks
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

1. **Pinecone Account**: Sign up at [pinecone.io](https://www.pinecone.io/) and get an API key
2. **Ollama** (recommended for local LLM):
   - Install from [ollama.ai](https://ollama.ai/)
   - Pull models:
     ```bash
     ollama pull llama3.1
     ollama pull nomic-embed-text
     ```
3. **(Optional)** OpenAI API key for GPT models
4. **(Optional)** Anthropic API key for Claude models

### Local Development Setup

#### 1. Clone and Setup Environment

```bash
cd "AI Rag 222"

# Backend setup
cd backend
cp .env.example .env
# Edit .env and add your Pinecone API key

# Frontend setup
cd ../frontend
cp .env.example .env
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python -m app.main
# or
uvicorn app.main:app --reload
```

Backend will run at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run at: `http://localhost:5173`

### Docker Deployment

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env and add your Pinecone API key

# 2. Start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## 📖 Usage Guide

### 1. Upload Documents

1. Navigate to the **Upload** page
2. Drag & drop or click to select a PDF or TXT file (max 15MB)
3. Click "Upload & Index Document"
4. Wait for processing (extraction → chunking → embedding → indexing)

### 2. Chat with Documents

1. Navigate to the **Chat** page
2. Select your preferred LLM provider (Ollama/OpenAI/Anthropic)
3. (Optional) Filter documents using the left sidebar
4. Type your question and press Enter
5. View answer with citations below each response

### Example Questions

- "What is the data retention policy?"
- "Summarize the compliance requirements for GDPR"
- "What are the procedures for incident reporting?"

## 🔧 Configuration

### Backend Environment Variables

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/policyrag

# Pinecone (REQUIRED)
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=policy-rag
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
EMBED_DIM=768

# Ollama (Default)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text

# OpenAI (Optional)
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini

# Anthropic (Optional)
ANTHROPIC_API_KEY=
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-latest

# Security (Optional)
API_KEY=  # If set, requires X-API-Key header
```

### Embedding Dimension Notes

The `EMBED_DIM` setting must match your embedding model:

- Ollama `nomic-embed-text`: 768
- OpenAI `text-embedding-3-small`: 1536
- OpenAI `text-embedding-ada-002`: 1536

## 📊 API Endpoints

### Documents

- `POST /api/docs/upload` - Upload document
- `GET /api/docs` - List all documents
- `GET /api/docs/{doc_id}` - Get document metadata

### Chat

- `POST /api/chat` - Send question

Request body:

```json
{
  "user_id": "user-123",
  "provider": "ollama",
  "model": "llama3.1",
  "question": "What is the policy?",
  "doc_ids": ["uuid-1", "uuid-2"],
  "top_k": 5
}
```

Response:

```json
{
  "answer": "According to the policy...",
  "citations": [
    {
      "doc_id": "uuid-1",
      "filename": "policy.pdf",
      "page_number": 3,
      "chunk_index": 5,
      "score": 0.89
    }
  ],
  "model": {
    "provider": "ollama",
    "name": "llama3.1"
  }
}
```

## 🗄️ Database Schema

### Documents Table

```sql
CREATE TABLE documents (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    preview_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Chat Audits Table

```sql
CREATE TABLE chat_audits (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    provider VARCHAR NOT NULL,
    model VARCHAR NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    cited_doc_ids VARCHAR[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔍 RAG Pipeline

1. **Retrieval Node**:
   - Generate query embedding
   - Search Pinecone for top-k similar chunks
   - Apply document filters if specified
   - Return citations with metadata

2. **Generation Node**:
   - Build system prompt for legal/compliance context
   - Format context from retrieved chunks
   - Call selected LLM
   - Return answer

3. **Audit**:
   - Log question, answer, model, and citations to PostgreSQL

## 🛠️ Development

### Adding a New LLM Provider

1. Update `backend/app/rag/llms.py`:

   ```python
   def get_llm(provider: str, model: Optional[str] = None):
       if provider == "new_provider":
           return NewProviderChat(model=model)
   ```

2. Update frontend `ModelPicker.jsx` to add UI option

### Changing Chunking Strategy

Edit `backend/app/core/config.py`:

```python
chunk_size: int = 1000
chunk_overlap: int = 150
```

## 🔒 Security Features

- Filename sanitization to prevent path traversal
- File size limits (configurable)
- Optional API key authentication
- CORS configuration
- Input validation with Pydantic
- Safe logging (no credentials or document text)

## 🐛 Troubleshooting

### Ollama Connection Error

```bash
# Check Ollama is running
ollama list

# Pull required models
ollama pull llama3.1
ollama pull nomic-embed-text

# Test Ollama API
curl http://localhost:11434/api/tags
```

### Pinecone Index Not Found

The index is created automatically on first use. Ensure:

1. `PINECONE_API_KEY` is set correctly
2. `EMBED_DIM` matches your embedding model
3. Backend has internet access

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Or if running locally
psql -U postgres -l
```

## 📈 Performance Tips

1. **Embeddings**: Use Ollama locally for free, unlimited embeddings
2. **Chunking**: Adjust `chunk_size` based on document complexity
3. **Top-k**: Start with 5, increase if answers lack context
4. **Caching**: React Query caches document list automatically

## 🤝 Contributing

This is a teaching/demo project. Feel free to fork and customize for your needs.

## 📝 License

MIT License - feel free to use for personal or commercial projects.

## 🙏 Acknowledgments

- LangChain & LangGraph for RAG orchestration
- Pinecone for vector search
- Ollama for local LLM inference
- FastAPI for the excellent Python web framework

---

**Happy Document Querying! 📄🤖**
# RAG-Multi-Agents-AI-React-App_-
# RAG-Multi-Agents-AI-React-App_-
# RAG-Multi-Agents-AI-React-App_-
