@echo off
echo ========================================
echo JARVIS Desktop App - Debug Launcher
echo ========================================
echo.

echo Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.11 from https://python.org
    pause
    exit /b 1
)
echo Python: OK
echo.

echo Checking Node.js...
node --version
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)
echo Node.js: OK
echo.

echo Checking if API server is already running...
netstat -ano | findstr :5000
if %errorlevel% equ 0 (
    echo WARNING: Port 5000 is already in use!
    echo Please close any other application using port 5000
    pause
)
echo.

echo Starting JARVIS Desktop App...
echo.
echo Console output will appear below:
echo ========================================
echo.

npm start

pause
