#!/usr/bin/env pwsh
# PowerShell script to start PolicyRAG application
# Works in PowerShell, Git Bash, and VS Code terminal

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Policy RAG Application - Startup Script" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"

# Check if Ollama is running (optional)
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "[OK] Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Ollama not detected - app will work in demo mode" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[START] Starting Backend Server (Port 8001)..." -ForegroundColor Cyan

# Start backend in new window
$BackendCmd = "cd '$BackendDir'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $BackendCmd

Start-Sleep -Seconds 3

Write-Host "[START] Starting Frontend Dev Server (Port 5173)..." -ForegroundColor Cyan

# Start frontend in new window
$FrontendCmd = "cd '$FrontendDir'; npm run dev"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $FrontendCmd

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "   Services Started Successfully!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8001" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8001/docs" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Cyan

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "Press any key to exit this window (servers will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
