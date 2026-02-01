@echo off
echo ======================================================================
echo   Policy RAG Application - Startup Script
echo ======================================================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Ollama not found in PATH
    echo           Install from: https://ollama.ai
    echo           The app will work in demo mode without it.
    echo.
    timeout /t 3 >nul
) else (
    echo [CHECK] Ollama found - checking if running...
    curl -s http://localhost:11434/api/tags >nul 2>nul
    if %errorlevel% neq 0 (
        echo [START] Starting Ollama server...
        start "Ollama Server" cmd /c ollama serve
        timeout /t 3 >nul
    ) else (
        echo [OK] Ollama already running
    )
)

echo.
echo [START] Starting Backend Server (Port 8005)...
start "Backend - Policy RAG API" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005"
timeout /t 5 >nul

echo [START] Starting Frontend Dev Server (Port 5173)...
start "Frontend - Policy RAG UI" cmd /k "cd /d "%~dp0frontend" && npm run dev"
timeout /t 5 >nul

echo.
echo ======================================================================
echo   Services Started Successfully!
echo ======================================================================
echo   Backend:  http://localhost:8005
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8005/docs
echo.
echo   Press any key to open the app in your browser...
echo ======================================================================
pause >nul

start http://localhost:5173

echo.
echo App opened! Close this window anytime - services will keep running.
echo To stop services, close the "Backend" and "Frontend" terminal windows.
