@echo off
echo ========================================
echo   AI Chatbot - Quick EXE Builder
echo ========================================
echo.

echo [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
) else (
    echo PyInstaller is already installed!
)

echo.
echo [2/4] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo.
echo [3/4] Building EXE (this may take 5-10 minutes)...
echo Please wait...

python build_exe.py

echo.
echo [4/4] Build complete!
echo.
echo ========================================
echo Location: dist\KAI_OS
echo.
echo Next steps:
echo 1. Ensure your .env file is configured in the dist\KAI_OS folder
echo 2. Run Start_KAI_OS.bat or dist\KAI_OS\KAI_OS.exe
echo 3. Share the dist folder with users
echo.
pause
