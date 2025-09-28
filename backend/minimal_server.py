#!/usr/bin/env python3
"""
Minimal server for testing
"""

from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple in-memory storage
profiles = {}
conversations = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "message": "Server is running",
        "status": "healthy"
    }), 200

@app.route('/store', methods=['POST'])
def store_profile():
    """Store a profile"""
    try:
        data = request.get_json()
        profile_id = str(uuid.uuid4())
        
        profiles[profile_id] = {
            "id": profile_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        return jsonify({
            "message": "Profile stored successfully",
            "id": profile_id,
            "status": "success"
        }), 201
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/list', methods=['GET'])
def list_profiles():
    """List all profiles"""
    try:
        ids = list(profiles.keys())
        return jsonify({
            "message": f"Found {len(ids)} profiles",
            "ids": ids,
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/conversation', methods=['POST'])
def store_conversation():
    """Store a conversation"""
    try:
        data = request.get_json()
        conversation_id = str(uuid.uuid4())
        
        message = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "agent_id": data.get('agent_id'),
            "message": data.get('message'),
            "sender": data.get('sender')
        }
        
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        conversations[conversation_id].append(message)
        
        return jsonify({
            "message": "Conversation stored successfully",
            "conversation_id": conversation_id,
            "status": "success"
        }), 201
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    logger.info("Starting minimal server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
