#!/bin/bash
# Bash script to start PolicyRAG application
# Works in Git Bash and WSL

echo "======================================================================"
echo "   Policy RAG Application - Startup Script"
echo "======================================================================"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if Ollama is running (optional)
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[OK] Ollama is running"
else
    echo "[WARNING] Ollama not detected - app will work in demo mode"
fi

echo ""
echo "[START] Starting Backend Server (Port 8001)..."

# Start backend in background
cd "$BACKEND_DIR"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 3

echo "[START] Starting Frontend Dev Server (Port 5173)..."

# Start frontend in background
cd "$FRONTEND_DIR"
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

sleep 5

echo ""
echo "======================================================================"
echo "   Services Started Successfully!"
echo "======================================================================"
echo "   Backend:  http://localhost:8001"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8001/docs"
echo "======================================================================"
echo ""
echo "   Backend PID:  $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the servers, run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Opening browser..."

# Try to open browser (works on most systems)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5173
elif command -v open > /dev/null; then
    open http://localhost:5173
elif command -v start > /dev/null; then
    start http://localhost:5173
fi

echo ""
echo "Servers running in background. Check backend.log and frontend.log for output."
