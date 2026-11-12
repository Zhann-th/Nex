#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# NEX CORE VISION ENGINE — macOS / Linux One-Click Launcher
# ═══════════════════════════════════════════════════════════════════
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "==========================================================="
echo "   NEX CORE VISION ENGINE — INITIALIZING SYSTEM DEMO       "
echo "==========================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ to continue."
    exit 1
fi

# Setup Virtual Environment if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating local virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "🔄 Activating virtual environment..."
source .venv/bin/activate

echo "📥 Verifying required dependencies (OpenCV, FastAPI, Uvicorn)..."
pip install -q -r requirements.txt

echo "==========================================================="
echo "🚀 Starting NEX Server with Object Database & Live Feeds..."
echo "📍 Dashboard: http://localhost:8000/dashboard"
echo "📍 Landing:   http://localhost:8000"
echo "==========================================================="

python3 nex_server.py --port 8000
