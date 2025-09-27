#!/bin/bash

# JSON Storage Server Startup Script

echo "🚀 Starting JSON Storage Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "🌐 Starting server on http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

python server.py
