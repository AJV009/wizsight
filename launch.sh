#!/bin/bash

# WizSight Launch Script
# Starts the FastAPI server and opens the dashboard in your browser

set -e

echo "🚀 Starting WizSight..."

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run from the wizsight directory."
    exit 1
fi

echo "📦 Installing dependencies..."
uv sync --quiet

# Start the server (try port 8001, fallback to 8002 if busy)
PORT=8001
if lsof -i :$PORT > /dev/null 2>&1; then
    PORT=8002
    echo "Port 8001 is busy, using port $PORT instead"
fi

echo "🌐 Starting WizSight API server on http://localhost:$PORT"
echo "🎛️  Dashboard will be available at: http://localhost:$PORT"
echo "📚 API Documentation at: http://localhost:$PORT/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

uv run uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --reload