@echo off
REM KAI OS - Production Start Script
REM =================================
REM Run this script to start the server in production mode

echo.
echo ========================================
echo    KAI OS - Production Mode
echo ========================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.production.template to .env and configure it.
    echo.
    pause
    exit /b 1
)

REM Set production environment
set FLASK_ENV=production
set PYTHONUNBUFFERED=1

REM Validate critical environment variables
python -c "from Config.production import validate_config; validate_config()" 2>nul
if errorlevel 1 (
    echo [ERROR] Configuration validation failed!
    echo Please check your .env file.
    pause
    exit /b 1
)

echo [OK] Configuration validated
echo.

REM Check for Gunicorn (Windows alternative: waitress)
python -c "import waitress" 2>nul
if errorlevel 1 (
    echo [INFO] Installing waitress for production serving...
    pip install waitress
)

echo [INFO] Starting KAI OS in production mode...
echo [INFO] API will be available at http://localhost:5000
echo [INFO] Press Ctrl+C to stop
echo.
echo ========================================
echo.

REM Start with Waitress (Windows WSGI server)
python -c "from waitress import serve; from api_server import app; print('[SERVER] Starting on port 5000...'); serve(app, host='0.0.0.0', port=5000, threads=4)"

pause
