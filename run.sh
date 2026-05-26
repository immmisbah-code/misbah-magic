#!/bin/bash
# ✨ Misbah's Magic — Quick Start Script

echo "✨ Starting Misbah's Magic..."
echo ""

cd "$(dirname "$0")"

# Install dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
  echo "📦 Installing Python dependencies..."
  pip3 install -r backend/requirements.txt --break-system-packages -q
fi

# Start backend
echo "🚀 Backend starting on http://localhost:5000"
echo "🌐 Open frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 backend/app.py
