# WebSocket Conversation System

This document describes the real-time conversation system with special shareable links for oParley.

## 🚀 Quick Start

### Start All Servers
```bash
./start_all_servers.sh
```

This will start:
- **Frontend**: http://localhost:3000
- **Main API**: http://localhost:8080  
- **WebSocket API**: http://localhost:8081

### Manual Start
```bash
# Terminal 1 - Main API Server
cd backend
source venv/bin/activate
python server.py

# Terminal 2 - WebSocket Server
cd backend
source venv/bin/activate
python websocket_server.py

# Terminal 3 - Frontend
cd frontend
npm run dev
```

## 🔗 Special Conversation Links

### Creating a Conversation
1. Go to http://localhost:3000/conversations
2. Click "Create New Conversation"
3. Fill in title and description
4. Get a shareable link like: `http://localhost:3000/conversation/abc12345`

### Joining a Conversation
1. Click the shareable link or visit `/conversation/{roomId}`
2. Enter your name
3. Start chatting in real-time!

## 📡 API Endpoints

### WebSocket Server (Port 8081)

#### REST Endpoints
- `POST /api/conversations/create` - Create new conversation
- `POST /api/conversations/{roomId}/join` - Join existing conversation
- `GET /api/conversations/{roomId}` - Get conversation details
- `GET /api/conversations` - List all active conversations
- `POST /api/conversations/{roomId}/end` - End a conversation
- `GET /api/health` - Health check

#### WebSocket Events
- `join_room` - Join a conversation room
- `leave_room` - Leave a conversation room
- `send_message` - Send a message
- `typing` - Send typing indicator
- `disconnect` - Handle disconnection

#### WebSocket Event Responses
- `conversation_state` - Current conversation data
- `new_message` - New message received
- `user_joined` - User joined notification
- `user_left` - User left notification
- `user_typing` - Typing indicator
- `conversation_ended` - Conversation ended
- `error` - Error message

## 🏗️ Architecture

### Backend Components
1. **websocket_server.py** - WebSocket server with Flask-SocketIO
2. **server.py** - Main REST API server
3. **conversation_api.py** - Legacy conversation API

### Frontend Components
1. **ConversationManager.tsx** - Create and manage conversations
2. **conversation/[roomId]/page.tsx** - Join and participate in conversations
3. **conversations/page.tsx** - List all conversations

### Data Flow
```
User creates conversation → WebSocket Server → Generates room ID → Returns shareable link
User clicks link → Frontend loads → Connects to WebSocket → Joins room → Real-time chat
```

## 🔧 Configuration

### CORS Settings
Both servers are configured for localhost development:
- Frontend: `http://localhost:3000`
- Alternative: `http://127.0.0.1:3000`

### Port Configuration
- Frontend: 3000
- Main API: 8080
- WebSocket API: 8081

## 📱 Features

### Real-time Features
- ✅ Live messaging
- ✅ Typing indicators
- ✅ User join/leave notifications
- ✅ Connection status
- ✅ Message timestamps

### Conversation Management
- ✅ Create conversations with custom titles/descriptions
- ✅ Generate shareable links
- ✅ Join existing conversations
- ✅ List active conversations
- ✅ End conversations
- ✅ Participant tracking

### UI Features
- ✅ Responsive design
- ✅ Real-time status indicators
- ✅ Copy-to-clipboard functionality
- ✅ Error handling
- ✅ Loading states

## 🛠️ Development

### Adding New Features
1. **Backend**: Add new endpoints in `websocket_server.py`
2. **Frontend**: Update components in `/components` or `/app`
3. **WebSocket Events**: Add new events in both server and client

### Testing
1. Create a conversation
2. Copy the shareable link
3. Open in multiple browser tabs/windows
4. Test real-time messaging
5. Test typing indicators
6. Test user join/leave

## 🐛 Troubleshooting

### Common Issues
1. **WebSocket connection failed**: Check if port 8081 is available
2. **CORS errors**: Verify CORS settings in both servers
3. **Frontend not loading**: Check if port 3000 is available
4. **API not responding**: Check if port 8080 is available

### Debug Mode
All servers run in debug mode with detailed logging. Check console output for errors.

## 📋 Example Usage

### Creating a Conversation via API
```bash
curl -X POST http://localhost:8081/api/conversations/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Conversation",
    "description": "A test conversation",
    "user_id": "user123"
  }'
```

### Joining a Conversation via API
```bash
curl -X POST http://localhost:8081/api/conversations/abc12345/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user456",
    "username": "John Doe"
  }'
```

### WebSocket Connection (JavaScript)
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8081');

socket.emit('join_room', {
  room_id: 'abc12345',
  user_id: 'user123',
  username: 'John Doe'
});

socket.on('new_message', (message) => {
  console.log('New message:', message);
});
```

## 🎯 Next Steps

Potential enhancements:
- Message persistence in database
- File sharing capabilities
- Voice/video calling integration
- Message encryption
- User authentication
- Conversation search
- Message reactions
- Push notifications
