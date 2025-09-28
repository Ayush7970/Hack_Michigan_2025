#!/bin/bash

echo "🧹 Cleaning up and starting fresh..."

# Kill any existing processes on ports 3000, 3001, 8080, 8081
echo "🛑 Stopping existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

# Wait a moment for ports to be released
sleep 2

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $WEBSOCKET_PID $FRONTEND_PID 2>/dev/null || true
    exit
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🚀 Starting WebSocket server on port 8081..."
cd backend
source venv/bin/activate
python simple_websocket_server.py &
WEBSOCKET_PID=$!

# Wait for WebSocket server to start
sleep 3

echo "🎨 Starting frontend on port 3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ System started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 WebSocket API: http://localhost:8081"
echo "💬 Conversations: http://localhost:3000/conversations"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for any process to exit
wait
