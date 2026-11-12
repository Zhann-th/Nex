@echo off
REM ═══════════════════════════════════════════════════════════════════
REM NEX CORE VISION ENGINE — Windows One-Click Launcher
REM ═══════════════════════════════════════════════════════════════════

cd /d "%~dp0"
echo ===========================================================
echo    NEX CORE VISION ENGINE — INITIALIZING SYSTEM DEMO
echo ===========================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [*] Installing / checking dependencies...
pip install -r requirements.txt

echo ===========================================================
echo [OK] Starting NEX Server...
echo [>] Open http://localhost:8000/dashboard in your browser!
echo ===========================================================

python nex_server.py --port 8000
pause
