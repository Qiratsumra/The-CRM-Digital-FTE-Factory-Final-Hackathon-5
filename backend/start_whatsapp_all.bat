@echo off
REM Start All Services - WhatsApp + Backend + Frontend
REM 
REM This script starts all required services for WhatsApp integration:
REM 1. Go WhatsApp Bridge (must stay running)
REM 2. Backend API Server
REM 3. Message Processor Worker
REM 4. Frontend (optional)
REM
REM Usage: start_whatsapp_all.bat
REM
REM Requirements:
REM - Go installed and in PATH
REM - Python 3.14+ with UV
REM - Node.js 18+
REM - WhatsApp authenticated via QR code (first time only)

echo ============================================================
echo Starting Customer Success FTE with WhatsApp Integration
echo ============================================================
echo.

REM Check if Go is installed
where go >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Go is not installed or not in PATH
    echo Download from: https://go.dev/dl/
    pause
    exit /b 1
)
echo [OK] Go is installed
echo.

REM Check if WhatsApp bridge directory exists
if not exist "whatsapp-mcp\whatsapp-bridge" (
    echo [ERROR] WhatsApp MCP bridge directory not found
    echo Please clone the repository first:
    echo   git clone https://github.com/lharries/whatsapp-mcp.git
    pause
    exit /b 1
)
echo [OK] WhatsApp MCP bridge directory found
echo.

REM Check if bridge executable exists
if not exist "whatsapp-mcp\whatsapp-bridge\whatsapp-bridge.exe" (
    echo [WARN] Bridge executable not found. Building...
    cd whatsapp-mcp\whatsapp-bridge
    go build -o whatsapp-bridge.exe main.go
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to build bridge executable
        echo You may need to install MSYS2 with ucrt64 C compiler
        cd ..\..
        pause
        exit /b 1
    )
    cd ..\..
    echo [OK] Bridge executable built successfully
) else (
    echo [OK] Bridge executable found
)
echo.

REM Check if database exists
if not exist "whatsapp-mcp\whatsapp-bridge\store\messages.db" (
    echo [WARN] WhatsApp database not found
    echo This is the first run - you need to authenticate
    echo.
    echo Starting bridge for QR code authentication...
    echo SCAN THE QR CODE with your WhatsApp mobile app:
    echo   Settings ^> Linked Devices ^> Link a Device
    echo.
    echo Press Ctrl+C after authentication to continue...
    echo.
    cd whatsapp-mcp\whatsapp-bridge
    go run main.go
    cd ..\..
)
echo.

echo ============================================================
echo Starting Services
echo ============================================================
echo.

REM Start Go Bridge in Window 1
echo [1/4] Starting Go WhatsApp Bridge...
start "WhatsApp Bridge" cmd /k "cd whatsapp-mcp\whatsapp-bridge && echo Starting WhatsApp Bridge... && go run main.go"
timeout /t 3 /nobreak >nul

REM Start Backend API in Window 2
echo [2/4] Starting Backend API Server...
start "Backend API" cmd /k "echo Starting Backend API... && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul

REM Start Message Processor in Window 3
echo [3/4] Starting Message Processor Worker...
start "Message Processor" cmd /k "echo Starting Message Processor... && python -m src.workers.message_processor"
timeout /t 2 /nobreak >nul

REM Start Frontend in Window 4 (optional)
echo [4/4] Starting Frontend...
start "Frontend" cmd /k "cd ..\frontend && echo Starting Frontend... && npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo All Services Started!
echo ============================================================
echo.
echo Services running:
echo   1. WhatsApp Bridge  - http://localhost:8080
echo   2. Backend API      - http://localhost:8000
echo   3. Message Worker   - (background process)
echo   4. Frontend         - http://localhost:3000
echo.
echo API Documentation: http://localhost:8000/docs
echo Support Form: http://localhost:3000/support
echo.
echo To test WhatsApp:
echo   1. Send a message to your WhatsApp number
echo   2. Check Message Processor logs for ticket creation
echo   3. Wait for AI response (within 30 seconds)
echo.
echo To stop all services: Close all terminal windows
echo.
echo ============================================================

pause
