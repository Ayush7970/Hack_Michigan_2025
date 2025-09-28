from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# In-memory conversation storage
conversation_history: List[Dict[str, str]] = []
negotiation_complete = False

@app.route('/rest/post', methods=['POST'])
def send_message():
    """Handle message sending from frontend"""
    global conversation_history

    try:
        data = request.get_json()

        if not data or 'input' not in data or 'address' not in data:
            return jsonify({
                "success": False,
                "error": "Missing input or address"
            }), 400

        message = data['input']
        target_address = data['address']

        print(f"🔥 API: Received message: {message}")
        print(f"🎯 API: Target address: {target_address}")

        # Add user message to conversation history
        conversation_history.append({
            "role": "user",
            "content": message
        })

        print(f"📝 API: Added to conversation. Total messages: {len(conversation_history)}")

        # For now, simulate sending to agent and getting a response
        # TODO: Actually send to the uagent at target_address

        # Simulate a response (replace with actual agent communication)
        agent_response = f"I understand you need: {message}. Let me help you with that. What's your budget?"

        conversation_history.append({
            "role": "seller",
            "content": agent_response
        })

        print(f"🤖 API: Added agent response. Total messages: {len(conversation_history)}")

        return jsonify({
            "success": True,
            "message": "Message sent successfully"
        })

    except Exception as e:
        print(f"❌ API: Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/conversation', methods=['GET'])
def get_conversation():
    """Get current conversation history"""
    global conversation_history, negotiation_complete

    try:
        print(f"📊 API: Returning {len(conversation_history)} messages")

        return jsonify({
            "messages": conversation_history,
            "is_complete": negotiation_complete
        })

    except Exception as e:
        print(f"❌ API: Error getting conversation: {e}")
        return jsonify({
            "messages": [],
            "is_complete": False
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "conversation_length": len(conversation_history)
    })

if __name__ == '__main__':
    print("🚀 Starting Conversation API on http://localhost:8001")
    app.run(debug=True, host='0.0.0.0', port=8001)