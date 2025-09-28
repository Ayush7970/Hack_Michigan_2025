from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime
import logging
from typing import List, Dict, Any
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# In-memory storage for conversations and rooms
conversations: Dict[str, Dict[str, Any]] = {}
active_rooms: Dict[str, List[str]] = {}  # room_id -> list of session_ids
room_metadata: Dict[str, Dict[str, Any]] = {}  # room_id -> metadata

def generate_room_id():
    """Generate a unique room ID for conversations"""
    return str(uuid.uuid4())[:8]  # Short ID for easy sharing

def generate_conversation_link(room_id: str):
    """Generate a shareable link for joining a conversation"""
    return f"http://localhost:3000/conversation/{room_id}"

@app.route('/api/conversations/create', methods=['POST'])
def create_conversation():
    """Create a new conversation room and return the join link"""
    try:
        data = request.get_json() or {}
        
        # Generate unique room ID
        room_id = generate_room_id()
        
        # Create conversation metadata
        conversation_data = {
            "room_id": room_id,
            "created_at": datetime.now().isoformat(),
            "created_by": data.get('user_id', 'anonymous'),
            "title": data.get('title', f'Conversation {room_id}'),
            "description": data.get('description', ''),
            "messages": [],
            "participants": [],
            "is_active": True
        }
        
        # Store conversation
        conversations[room_id] = conversation_data
        active_rooms[room_id] = []
        room_metadata[room_id] = {
            "title": conversation_data["title"],
            "description": conversation_data["description"],
            "created_at": conversation_data["created_at"],
            "participant_count": 0
        }
        
        # Generate shareable link
        join_link = generate_conversation_link(room_id)
        
        logger.info(f"Created conversation room {room_id} with link: {join_link}")
        
        return jsonify({
            "success": True,
            "room_id": room_id,
            "join_link": join_link,
            "conversation": conversation_data
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/conversations/<room_id>/join', methods=['POST'])
def join_conversation(room_id: str):
    """Join an existing conversation room"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', f'User_{user_id[:6]}')
        
        if room_id not in conversations:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
        
        if not conversations[room_id]["is_active"]:
            return jsonify({
                "success": False,
                "error": "Conversation is no longer active"
            }), 400
        
        # Add participant to conversation
        participant = {
            "user_id": user_id,
            "username": username,
            "joined_at": datetime.now().isoformat()
        }
        
        if participant not in conversations[room_id]["participants"]:
            conversations[room_id]["participants"].append(participant)
            room_metadata[room_id]["participant_count"] = len(conversations[room_id]["participants"])
        
        logger.info(f"User {username} joined conversation {room_id}")
        
        return jsonify({
            "success": True,
            "room_id": room_id,
            "conversation": conversations[room_id],
            "join_link": generate_conversation_link(room_id)
        }), 200
        
    except Exception as e:
        logger.error(f"Error joining conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/conversations/<room_id>', methods=['GET'])
def get_conversation(room_id: str):
    """Get conversation details and messages"""
    try:
        if room_id not in conversations:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
        
        return jsonify({
            "success": True,
            "conversation": conversations[room_id]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """List all active conversations"""
    try:
        active_conversations = []
        for room_id, conv in conversations.items():
            if conv["is_active"]:
                active_conversations.append({
                    "room_id": room_id,
                    "title": conv["title"],
                    "description": conv["description"],
                    "created_at": conv["created_at"],
                    "participant_count": len(conv["participants"]),
                    "message_count": len(conv["messages"]),
                    "join_link": generate_conversation_link(room_id)
                })
        
        return jsonify({
            "success": True,
            "conversations": active_conversations
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/conversations/<room_id>/end', methods=['POST'])
def end_conversation(room_id: str):
    """End a conversation (make it inactive)"""
    try:
        if room_id not in conversations:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
        
        conversations[room_id]["is_active"] = False
        conversations[room_id]["ended_at"] = datetime.now().isoformat()
        
        # Notify all connected clients
        socketio.emit('conversation_ended', {
            "room_id": room_id,
            "message": "This conversation has ended"
        }, room=room_id)
        
        logger.info(f"Conversation {room_id} ended")
        
        return jsonify({
            "success": True,
            "message": "Conversation ended successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# WebSocket event handlers
@socketio.on('join_room')
def handle_join_room(data):
    """Handle client joining a conversation room"""
    try:
        room_id = data.get('room_id')
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', f'User_{user_id[:6]}')
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        if room_id not in conversations:
            emit('error', {'message': 'Conversation not found'})
            return
        
        if not conversations[room_id]["is_active"]:
            emit('error', {'message': 'Conversation is no longer active'})
            return
        
        # Join the SocketIO room
        join_room(room_id)
        
        # Add to active rooms tracking
        if room_id not in active_rooms:
            active_rooms[room_id] = []
        
        if request.sid not in active_rooms[room_id]:
            active_rooms[room_id].append(request.sid)
        
        # Add participant to conversation if not already there
        participant = {
            "user_id": user_id,
            "username": username,
            "joined_at": datetime.now().isoformat()
        }
        
        if participant not in conversations[room_id]["participants"]:
            conversations[room_id]["participants"].append(participant)
            room_metadata[room_id]["participant_count"] = len(conversations[room_id]["participants"])
        
        # Send current conversation state to the joining client
        emit('conversation_state', {
            'conversation': conversations[room_id],
            'room_id': room_id
        })
        
        # Notify other clients in the room
        emit('user_joined', {
            'user_id': user_id,
            'username': username,
            'participant_count': len(conversations[room_id]["participants"])
        }, room=room_id, include_self=False)
        
        logger.info(f"User {username} joined room {room_id} via WebSocket")
        
    except Exception as e:
        logger.error(f"Error in join_room: {e}")
        emit('error', {'message': str(e)})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle client leaving a conversation room"""
    try:
        room_id = data.get('room_id')
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', f'User_{user_id[:6]}')
        
        if room_id and room_id in active_rooms:
            if request.sid in active_rooms[room_id]:
                active_rooms[room_id].remove(request.sid)
            
            # Remove from SocketIO room
            leave_room(room_id)
            
            # Notify other clients
            emit('user_left', {
                'user_id': user_id,
                'username': username,
                'participant_count': len(active_rooms[room_id])
            }, room=room_id, include_self=False)
            
            logger.info(f"User {username} left room {room_id}")
        
    except Exception as e:
        logger.error(f"Error in leave_room: {e}")

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message in a conversation"""
    try:
        room_id = data.get('room_id')
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', f'User_{user_id[:6]}')
        message_type = data.get('type', 'text')  # text, system, etc.
        
        if not room_id or not message:
            emit('error', {'message': 'Room ID and message are required'})
            return
        
        if room_id not in conversations:
            emit('error', {'message': 'Conversation not found'})
            return
        
        if not conversations[room_id]["is_active"]:
            emit('error', {'message': 'Conversation is no longer active'})
            return
        
        # Create message object
        message_obj = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "username": username,
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to conversation history
        conversations[room_id]["messages"].append(message_obj)
        
        # Broadcast to all clients in the room
        emit('new_message', message_obj, room=room_id)
        
        logger.info(f"Message sent in room {room_id} by {username}: {message[:50]}...")
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        emit('error', {'message': str(e)})

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicators"""
    try:
        room_id = data.get('room_id')
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', f'User_{user_id[:6]}')
        is_typing = data.get('is_typing', False)
        
        if room_id:
            emit('user_typing', {
                'user_id': user_id,
                'username': username,
                'is_typing': is_typing
            }, room=room_id, include_self=False)
        
    except Exception as e:
        logger.error(f"Error in typing: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        # Remove from all active rooms
        for room_id, session_ids in active_rooms.items():
            if request.sid in session_ids:
                session_ids.remove(request.sid)
                logger.info(f"Client disconnected from room {room_id}")
        
    except Exception as e:
        logger.error(f"Error in disconnect: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "active_conversations": len([c for c in conversations.values() if c["is_active"]]),
        "total_conversations": len(conversations),
        "active_connections": sum(len(sessions) for sessions in active_rooms.values())
    })

if __name__ == '__main__':
    logger.info("🚀 Starting WebSocket Conversation Server...")
    logger.info("📡 WebSocket server will run on http://localhost:8081")
    logger.info("🔗 API endpoints available at http://localhost:8081/api/")
    
    # Start the server
    socketio.run(app, debug=True, host='0.0.0.0', port=8081)
