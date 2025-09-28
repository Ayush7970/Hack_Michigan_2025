#!/bin/bash

echo "🚀 Starting WebSocket Conversation System..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $WEBSOCKET_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the WebSocket server (port 8081)
echo "🔌 Starting WebSocket server on port 8081..."
cd backend
source venv/bin/activate
python simple_websocket_server.py &
WEBSOCKET_PID=$!

# Start the frontend (port 3000)
echo "🎨 Starting frontend on port 3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ WebSocket system started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 WebSocket API: http://localhost:8081"
echo "💬 Conversations: http://localhost:3000/conversations"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for any process to exit
wait
