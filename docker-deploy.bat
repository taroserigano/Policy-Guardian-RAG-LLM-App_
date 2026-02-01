@echo off
REM =============================================================================
REM Policy RAG - Docker Deployment Script (Windows)
REM =============================================================================
echo.
echo ======================================================================
echo   Policy RAG - Docker Deployment
echo ======================================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if .env.docker exists
if not exist ".env.docker" (
    echo [WARNING] .env.docker not found!
    echo.
    echo Creating .env.docker from template...
    copy ".env.docker.example" ".env.docker"
    echo.
    echo [ACTION REQUIRED] Please edit .env.docker and add your API keys:
    echo   - OPENAI_API_KEY
    echo   - PINECONE_API_KEY
    echo   - POSTGRES_PASSWORD (change the default!)
    echo.
    notepad .env.docker
    pause
    exit /b 1
)

echo [INFO] Building and starting containers...
echo.

REM Build and start containers
docker compose --env-file .env.docker up -d --build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker deployment failed!
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   Deployment Complete!
echo ======================================================================
echo.
echo   Frontend:  http://localhost
echo   Backend:   http://localhost:8001
echo   API Docs:  http://localhost:8001/docs
echo   Database:  PostgreSQL on localhost:5432
echo.
echo   Useful commands:
echo     docker compose logs -f        # View logs
echo     docker compose down           # Stop all services
echo     docker compose ps             # Check status
