@echo off
echo ======================================================================
echo   Policy RAG Application - Docker Startup
echo ======================================================================
echo.

REM Check if Docker is running
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo         Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [CHECK] Docker is running
echo.

echo [BUILD] Building Docker images...
docker-compose build

echo.
echo [START] Starting containers...
docker-compose up -d

echo.
echo [WAIT] Waiting for services to be ready...
timeout /t 5 >nul

echo.
echo ======================================================================
echo   Docker Services Started!
echo ======================================================================
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo.
echo   View logs: docker-compose logs -f
echo   Stop:      docker-compose down
echo ======================================================================
echo.
echo   Press any key to open the app in your browser...
pause >nul

start http://localhost:5173
