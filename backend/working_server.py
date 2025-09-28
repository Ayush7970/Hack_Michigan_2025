#!/usr/bin/env python3
"""
Working DynamoDB-based agent matching server
"""

from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from mock_dynamodb_service import MockDynamoDBService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Mock DynamoDB service
try:
    dynamodb_service = MockDynamoDBService()
    # Load existing data from files
    dynamodb_service.load_from_files()
    logger.info("Mock DynamoDB service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize DynamoDB service: {e}")
    dynamodb_service = None

# Initialize semantic model for better matching
logger.info("Loading semantic model for better matching...")
try:
    semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Semantic model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load semantic model: {e}")
    semantic_model = None

def generate_unique_id():
    """Generate a unique identifier for the data"""
    return str(uuid.uuid4())

def store_profile_data(profile_data, unique_id=None):
    """Store profile data in DynamoDB"""
    if dynamodb_service is None:
        logger.error("DynamoDB service not available")
        return False
    
    try:
        profile_id = dynamodb_service.store_profile(profile_data, unique_id)
        logger.info(f"Successfully stored profile data with ID: {profile_id}")
        return profile_id
    except Exception as e:
        logger.error(f"Error storing profile data: {str(e)}")
        return None

def retrieve_profile_data(unique_id):
    """Retrieve profile data by unique ID"""
    if dynamodb_service is None:
        logger.error("DynamoDB service not available")
        return None
    
    try:
        return dynamodb_service.retrieve_profile(unique_id)
    except Exception as e:
        logger.error(f"Error retrieving profile data: {str(e)}")
        return None

def get_all_stored_data():
    """Get all stored agent profiles"""
    if dynamodb_service is None:
        logger.error("DynamoDB service not available")
        return []
    
    try:
        return dynamodb_service.get_all_profiles()
    except Exception as e:
        logger.error(f"Error retrieving all data: {str(e)}")
        return []

def calculate_semantic_similarity(description1: str, description2: str) -> float:
    """Calculate semantic similarity between two descriptions using sentence transformers"""
    if semantic_model is None:
        # Fallback to basic similarity if model not available
        from difflib import SequenceMatcher
        return SequenceMatcher(None, description1.lower(), description2.lower()).ratio()
    
    try:
        # Encode both descriptions into embeddings
        embeddings = semantic_model.encode([description1, description2])
        
        # Calculate cosine similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {e}")
        # Fallback to basic similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, description1.lower(), description2.lower()).ratio()

def create_enhanced_description(uagent_data: Dict[str, Any]) -> str:
    """Create an enhanced description combining job, tags, and description for better matching"""
    job = uagent_data.get('job', '')
    tags = uagent_data.get('tags', [])
    description = uagent_data.get('description', '')
    
    # Combine all relevant information
    enhanced = f"{job} {description}"
    if tags:
        enhanced += f" Skills: {', '.join(tags)}"
    
    return enhanced

def find_best_match(request_description: str, uagents: List[Dict[str, Any]]) -> tuple:
    """Find the best matching uagent based on semantic similarity"""
    if not uagents:
        return None, 0.0
    
    best_match = None
    best_score = 0.0
    
    for uagent in uagents:
        uagent_data = uagent.get('data', {})
        
        # Create enhanced description for better matching
        enhanced_description = create_enhanced_description(uagent_data)
        
        # Calculate semantic similarity
        similarity = calculate_semantic_similarity(request_description, enhanced_description)
        
        # Additional boosts for exact keyword matches in job title
        job = uagent_data.get('job', '').lower()
        request_lower = request_description.lower()
        
        # Check for profession-specific keywords
        profession_keywords = {
            'plumber': ['plumb', 'pipe', 'drain', 'toilet', 'sink', 'water', 'sewer'],
            'carpenter': ['carpent', 'wood', 'furniture', 'cabinet', 'custom', 'build'],
            'mechanic': ['mechanic', 'auto', 'car', 'vehicle', 'engine', 'brake', 'repair'],
            'electrician': ['electric', 'wiring', 'outlet', 'light', 'power', 'electrical'],
            'doctor': ['doctor', 'medical', 'health', 'medicine', 'treatment', 'diagnosis']
        }
        
        job_boost = 0.0
        for profession, keywords in profession_keywords.items():
            if profession in job:
                for keyword in keywords:
                    if keyword in request_lower:
                        job_boost += 0.1
                        break
        
        total_score = similarity + job_boost
        
        if total_score > best_score:
            best_score = total_score
            best_match = uagent
    
    return best_match, best_score

@app.route('/store', methods=['POST'])
def store_json():
    """
    POST endpoint to store JSON data
    Expects JSON data in the request body
    Returns the unique ID assigned to the stored data
    """
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                "error": "Request must contain JSON data",
                "status": "error"
            }), 400
        
        # Get JSON data from request
        json_data = request.get_json()
        
        if json_data is None:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        # Store the profile data
        profile_id = store_profile_data(json_data)
        if profile_id:
            return jsonify({
                "message": "Profile data stored successfully",
                "id": profile_id,
                "status": "success"
            }), 201
        else:
            return jsonify({
                "error": "Failed to store profile data",
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in store_json endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/retrieve/<unique_id>', methods=['GET'])
def retrieve_json(unique_id):
    """
    GET endpoint to retrieve stored JSON data by unique ID
    """
    try:
        data = retrieve_profile_data(unique_id)
        
        if data is None:
            return jsonify({
                "error": "Profile data not found",
                "status": "error"
            }), 404
        
        return jsonify({
            "message": "Profile data retrieved successfully",
            "data": data,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in retrieve_json endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/list', methods=['GET'])
def list_stored_data():
    """
    GET endpoint to list all stored JSON data IDs
    """
    try:
        profiles = get_all_stored_data()
        ids = [profile['id'] for profile in profiles]
        
        return jsonify({
            "message": f"Found {len(ids)} stored profiles",
            "ids": ids,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in list_stored_data endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/match', methods=['POST'])
def match_uagent():
    """
    POST endpoint to find a matching uagent based on description
    Expects JSON data with 'description' field
    Returns the address of the best matching uagent
    """
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                "error": "Request must contain JSON data",
                "status": "error"
            }), 400
        
        # Get JSON data from request
        request_data = request.get_json()
        
        if request_data is None:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        # Check if description is provided
        if 'description' not in request_data:
            return jsonify({
                "error": "Description field is required for matching",
                "status": "error"
            }), 400
        
        request_description = request_data['description']
        
        # Get all stored uagents
        uagents = get_all_stored_data()
        
        if not uagents:
            return jsonify({
                "error": "No uagents available for matching",
                "status": "error"
            }), 404
        
        # Find the best match
        best_match, match_score = find_best_match(request_description, uagents)
        
        if best_match is None:
            return jsonify({
                "error": "No suitable match found",
                "status": "error"
            }), 404
        
        # Extract the matched uagent's data
        matched_data = best_match.get('data', {})
        matched_address = matched_data.get('address', '')
        
        if not matched_address:
            return jsonify({
                "error": "Matched uagent has no address",
                "status": "error"
            }), 500
        
        logger.info(f"Found match with score {match_score:.2f} for description: {request_description[:50]}...")
        
        return jsonify({
            "message": "Match found successfully",
            "matched_address": matched_address,
            "match_score": round(match_score, 3),
            "matched_uagent": {
                "name": matched_data.get('name', ''),
                "job": matched_data.get('job', ''),
                "description": matched_data.get('description', ''),
                "tags": matched_data.get('tags', []),
                "averagePrice": matched_data.get('averagePrice', 0)
            },
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in match_uagent endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/conversation', methods=['POST'])
def store_conversation():
    """
    POST endpoint to store a conversation message
    Expects JSON data with 'agent_id', 'message', 'sender', and optional 'conversation_id'
    """
    try:
        if not request.is_json:
            return jsonify({
                "error": "Request must contain JSON data",
                "status": "error"
            }), 400
        
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        # Validate required fields
        required_fields = ['agent_id', 'message', 'sender']
        for field in required_fields:
            if field not in request_data:
                return jsonify({
                    "error": f"Missing required field: {field}",
                    "status": "error"
                }), 400
        
        # Store conversation
        conversation_id = dynamodb_service.store_conversation(
            agent_id=request_data['agent_id'],
            message=request_data['message'],
            sender=request_data['sender'],
            conversation_id=request_data.get('conversation_id')
        )
        
        return jsonify({
            "message": "Conversation stored successfully",
            "conversation_id": conversation_id,
            "status": "success"
        }), 201
        
    except Exception as e:
        logger.error(f"Error in store_conversation endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """
    GET endpoint to retrieve a conversation by ID
    """
    try:
        messages = dynamodb_service.get_conversation(conversation_id)
        
        return jsonify({
            "message": "Conversation retrieved successfully",
            "conversation_id": conversation_id,
            "messages": messages,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_conversation endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/agent/<agent_id>/conversations', methods=['GET'])
def get_agent_conversations(agent_id):
    """
    GET endpoint to retrieve all conversations for an agent
    """
    try:
        conversations = dynamodb_service.get_agent_conversations(agent_id)
        
        return jsonify({
            "message": "Agent conversations retrieved successfully",
            "agent_id": agent_id,
            "conversations": conversations,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_agent_conversations endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "message": "Server is running",
        "status": "healthy"
    }), 200

if __name__ == '__main__':
    logger.info("Starting DynamoDB-based agent matching server...")
    if dynamodb_service:
        logger.info("DynamoDB service is ready")
    else:
        logger.warning("DynamoDB service is not available - some features may not work")
    app.run(debug=True, host='127.0.0.1', port=3000)
