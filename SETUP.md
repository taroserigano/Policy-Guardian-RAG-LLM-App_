# Setup Guide - Policy RAG Application

## Quick Start

**Windows:** Double-click `start.bat` in the project root. It will:

- ✅ Check and start Ollama (if installed)
- ✅ Start the backend server
- ✅ Start the frontend dev server
- ✅ Open the app in your browser

**That's it!** The app will be running at `http://localhost:5173`

---

## One-Time Prerequisites

### 1. Python Environment

```bash
cd backend
pip install fastapi uvicorn python-multipart requests python-dotenv
```

**Note:** We use `simple_server.py` which has minimal dependencies. The full app (`app/main.py`) requires additional packages but has dependency conflicts - stick with simple_server.

### 2. Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. LLM Provider (Choose One)

#### Option A: Ollama (Free, Local) - **Recommended**

1. Download from https://ollama.ai
2. Install and run: `ollama serve`
3. Pull a model: `ollama pull llama3.1`

#### Option B: OpenAI (Paid)

Set environment variable in `backend/.env`:

```
OPENAI_API_KEY=sk-your-key-here
```

#### Option C: Anthropic (Paid)

Set environment variable in `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Environment File (Optional)

Copy `env-sample` to `backend/.env` and fill in your API keys:

```bash
cd backend
cp ../env-sample .env
```

---

## Manual Start (Alternative)

If you prefer to start services manually:

### Terminal 1 - Ollama (if using local LLM)

```bash
ollama serve
```

### Terminal 2 - Backend

```bash
cd backend
python simple_server.py
```

### Terminal 3 - Frontend

```bash
cd frontend
npm run dev
```

Then open http://localhost:5173

---

## Troubleshooting

### Backend won't start

- Make sure Python 3.12+ is installed
- Install minimal dependencies: `pip install fastapi uvicorn python-multipart requests python-dotenv`
- Use `simple_server.py` (NOT `app/main.py` which has dependency issues)

### LLM returns demo responses

- Install Ollama from https://ollama.ai
- Run `ollama serve` in a terminal
- Pull a model: `ollama pull llama3.1`

### Frontend shows "Network Error"

- Check backend is running on port 8001
- Backend terminal should show: "Uvicorn running on http://0.0.0.0:8001"

### Port already in use

- Backend (8001): Change port in `simple_server.py` line 377
- Frontend (5173): Change port in `vite.config.js`

---

## Architecture Overview

### Current Setup (Simple Mode)

- **Backend:** `simple_server.py` - Minimal FastAPI server with in-memory storage
- **Features:** Document upload, RAG chat, LLM switching (Ollama/OpenAI/Anthropic)
- **Limitations:** No database persistence, simplified retrieval

### Full Setup (Not Working - Dependency Issues)

- **Backend:** `app/main.py` - Full FastAPI app with PostgreSQL + Pinecone
- **Issues:** langgraph, scikit-learn, numpy version conflicts
- **Status:** Abandoned for now - use simple_server instead

---

## Production Deployment

For production, you'll need to:

1. Fix dependency conflicts in `app/main.py`
2. Set up PostgreSQL database
3. Configure Pinecone vector store
4. Use gunicorn/uvicorn workers
5. Build frontend: `npm run build`
6. Serve frontend build with nginx/caddy

For now, `simple_server.py` is perfect for development and demos.

---

## Docker (Optional)

If you prefer Docker:

```bash
docker-compose up -d
```

Or use `start-docker.bat` on Windows.

**Note:** The app is designed to run locally. Docker adds complexity without benefits for this use case.
