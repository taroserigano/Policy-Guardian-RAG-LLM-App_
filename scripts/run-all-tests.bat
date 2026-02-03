@echo off
REM Comprehensive Test Runner for RAG Application
REM Runs all tests: Backend (pytest) and Frontend (Playwright)

echo ========================================
echo    RAG Application - Test Suite
echo ========================================
echo.

REM Check if servers are running
echo [1/4] Checking servers...
curl -s http://localhost:8001/docs > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Backend server not detected on port 8001
    echo Please start the backend server first: cd backend ^&^& python run_server.py
) else (
    echo [OK] Backend server running
)

curl -s http://localhost:5173 > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Frontend server not detected on port 5173
    echo Please start the frontend server first: cd frontend ^&^& npm run dev
) else (
    echo [OK] Frontend server running
)

echo.
echo ========================================
echo [2/4] Running Backend Tests (pytest)
echo ========================================
cd backend

REM Run pytest with verbose output
python -m pytest tests/ -v --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some backend tests failed
) else (
    echo [OK] Backend tests passed
)

echo.
echo ========================================
echo [3/4] Running E2E Tests (Playwright)
echo ========================================
cd ../frontend

REM Install playwright browsers if needed
call npx playwright install chromium --with-deps 2>nul

REM Run Playwright tests
call npx playwright test --reporter=list

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some E2E tests failed
    echo Run 'npx playwright show-report' to see detailed results
) else (
    echo [OK] E2E tests passed
)

echo.
echo ========================================
echo [4/4] Test Summary
echo ========================================
echo.
echo Test locations:
echo   Backend:  backend/tests/
echo   E2E:      frontend/e2e/
echo.
echo To run individual test suites:
echo   Backend:  cd backend ^&^& python -m pytest tests/ -v
echo   E2E:      cd frontend ^&^& npx playwright test
echo.
echo To see E2E report: cd frontend ^&^& npx playwright show-report
echo.
echo ========================================
cd ..
