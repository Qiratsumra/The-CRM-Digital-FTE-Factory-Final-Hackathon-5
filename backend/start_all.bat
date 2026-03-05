@echo off
echo ========================================
echo  Customer Success FTE - Startup Script
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "whatsapp-mcp\whatsapp-bridge\main.go" (
    echo ERROR: Please run this script from D:\Hackathon_05\backend
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo [1/3] Starting WhatsApp Bridge...
echo.
start "WhatsApp Bridge" cmd /k "cd /d %CD%\whatsapp-mcp\whatsapp-bridge && echo Starting WhatsApp MCP Bridge... && go run main.go"

echo Waiting for WhatsApp Bridge to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo.
echo [2/3] Starting Backend API Server...
echo.
start "Backend API" cmd /k "cd /d %CD% && echo Starting Backend API on port 8000... && uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for Backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Starting Frontend...
echo.
start "Frontend" cmd /k "cd /d %CD%\..\frontend && echo Starting Frontend on port 3000... && npm run dev"

echo.
echo ========================================
echo  All Services Started Successfully!
echo ========================================
echo.
echo Services:
echo   ✓ WhatsApp Bridge  → Port 8080
echo   ✓ Backend API      → Port 8000 (http://localhost:8000)
echo   ✓ Frontend         → Port 3000 (http://localhost:3000)
echo.
echo URLs:
echo   • Frontend:        http://localhost:3000
echo   • API Docs:        http://localhost:8000/docs
echo   • WhatsApp Setup:  http://localhost:3000/support/whatsapp/setup
echo.
echo To stop all services: Close all terminal windows
echo ========================================
echo.
pause
