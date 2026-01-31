# PolicyRAG - Quick Start Guide

## ⚠️ FIRST TIME SETUP (Required!)

Before starting the app, you MUST complete these one-time setup steps:

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Create Environment File

The `.env` file is **already created** in `backend/.env` with your Neon database connection.

**Important**: Verify these settings are correct:

- `DATABASE_URL` must use `postgresql://` (not `postgres://`)
- `CORS_ORIGINS` must be JSON array: `["http://localhost:5173"]`
- `PINECONE_API_KEY` - add your key for vector search
- Optional: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` for cloud LLMs

### 4. Database

✅ **Already configured!** Using Neon PostgreSQL cloud database.

The database tables will be created automatically on first startup.

### 5. Optional: Install Ollama (Free Local LLM)

Download from https://ollama.ai and run:

```bash
ollama serve
ollama pull llama3.1
```

**✅ Setup complete!** Now you can start the application.

---

## 🚀 Starting the Application

**Recommended method (works on all platforms):**

```bash
node start-dev.js
```

This launches both:

- **Backend** (FastAPI/Python) on port 8001
- **Frontend** (React/Vite) on port 5173+

Your browser will open automatically to the frontend URL.

**Alternative methods:**

### Windows Batch File

Double-click `start.bat` in Windows Explorer

### PowerShell Script

```powershell
./start.ps1
```

### Bash Script (Git Bash/WSL/Linux)

```bash
chmod +x start.sh
./start.sh
```

---

## 📦 What Gets Started

All methods start:

- **Backend API** on http://localhost:8001
- **Frontend UI** on http://localhost:5173
- **API Documentation** at http://localhost:8001/docs

Your browser will automatically open to http://localhost:5173

---

## 🛑 Stopping the Application

- **Node.js launcher:** Press `Ctrl+C` in the terminal
- **PowerShell/Bash:** Press `Ctrl+C` or close the terminal windows
- **Batch file:** Close the command windows

If servers don't stop properly:

```bash
# Find process on port 8001
netstat -ano | findstr :8001

# Kill it (replace PID with the number from above)
taskkill //PID <PID> //F
```

---

## 🔧 Troubleshooting

### "Port already in use" error?

**Backend (port 8001):**

```bash
# Find the process
netstat -ano | findstr :8001

# Kill it (Windows)
taskkill //PID <PID> //F
```

**Frontend (port 5173):**
Vite automatically tries the next available port (5174, 5175, etc.)

### Backend not starting or "Server unreachable"?

1. **Check .env file exists**: `backend/.env` should exist with your database connection
2. **Verify DATABASE_URL format**: Must be `postgresql://` not `postgres://`
3. **Verify CORS_ORIGINS format**: Must be `["http://localhost:5173"]` (JSON array)
4. **Check Python packages**: `cd backend && pip install -r requirements.txt`
5. **Restart after code changes**: Backend requires restart to load changes

**Manual diagnostic:**

```bash
# Check if backend dependencies are installed
cd backend
python -c "import fastapi, uvicorn, langchain; print('Dependencies OK')"

# Manually start backend to see error messages
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Common fixes:

- **Port already in use**: Kill the old process (see above)
- **Database errors**: Check `DATABASE_URL` in `backend/.env`
- **Missing packages**: Run `pip install -r requirements.txt` in backend folder
- **After code changes**: Stop app (`Ctrl+C`), kill port 8001 process, restart

---

## ✅ What You Should See

When running successfully:

- Backend logs: "Database tables created successfully"
- Backend logs: "Server startup complete - ready to accept requests"
- Frontend opens in browser at http://localhost:5173 (or 5174, 5175, etc.)
- No "Server unreachable" errors in the UI

---

## 📚 Next Steps

Once the app is running:

1. **Upload documents** (PDF/TXT) using the upload button
2. **Ask questions** about your documents in the chat interface
3. **Switch LLM providers** (Ollama/OpenAI/Anthropic) in settings
4. View **API documentation** at http://localhost:8001/docs

For detailed setup and configuration, see [SETUP.md](SETUP.md)
