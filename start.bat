@echo off
title KAI OS - Beast Mode Server
color 0A

echo.
echo  ================================
echo     KAI OS - Beast Mode Server
echo  ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo [INFO] Creating from .env.example...
    copy ".env.example" ".env" >nul
    echo [INFO] Please edit .env and add your API keys
    echo.
)

:: Start server
echo [INFO] Starting KAI OS server...
echo [INFO] Dashboard: http://localhost:5000/Frontend/dashboard.html
echo [INFO] Chat: http://localhost:5000/Frontend/chat.html
echo [INFO] API: http://localhost:5000/api/v1
echo.
echo Press Ctrl+C to stop the server
echo.

python api_server.py

pause
