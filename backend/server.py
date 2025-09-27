from flask import Flask, request, jsonify
import json
import os
import uuid
from datetime import datetime
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create storage directory if it doesn't exist
STORAGE_DIR = "json_storage"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# Initialize semantic model for better matching
logger.info("Loading semantic model for better matching...")
try:
    semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Semantic model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load semantic model: {e}")
    semantic_model = None

def generate_unique_id():
    """Generate a unique identifier for the JSON data"""
    return str(uuid.uuid4())

def store_json_data(json_data, unique_id):
    """Store JSON data to a file with the given unique ID"""
    filename = f"{unique_id}.json"
    filepath = os.path.join(STORAGE_DIR, filename)
    
    # Add metadata to the stored data
    data_with_metadata = {
        "id": unique_id,
        "timestamp": datetime.now().isoformat(),
        "data": json_data
    }
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data_with_metadata, f, indent=2)
        logger.info(f"Successfully stored JSON data with ID: {unique_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing JSON data: {str(e)}")
        return False

def retrieve_json_data(unique_id):
    """Retrieve JSON data by unique ID"""
    filename = f"{unique_id}.json"
    filepath = os.path.join(STORAGE_DIR, filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error retrieving JSON data: {str(e)}")
        return None

def get_all_stored_data():
    """Get all stored uagent data"""
    uagents = []
    
    if not os.path.exists(STORAGE_DIR):
        return uagents
    
    try:
        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(STORAGE_DIR, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    uagents.append(data)
    except Exception as e:
        logger.error(f"Error retrieving all data: {str(e)}")
    
    return uagents

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
        
        # Generate unique ID
        unique_id = generate_unique_id()
        
        # Store the JSON data
        if store_json_data(json_data, unique_id):
            return jsonify({
                "message": "JSON data stored successfully",
                "id": unique_id,
                "status": "success"
            }), 201
        else:
            return jsonify({
                "error": "Failed to store JSON data",
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
        data = retrieve_json_data(unique_id)
        
        if data is None:
            return jsonify({
                "error": "JSON data not found",
                "status": "error"
            }), 404
        
        return jsonify({
            "message": "JSON data retrieved successfully",
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
        if not os.path.exists(STORAGE_DIR):
            return jsonify({
                "message": "No data stored yet",
                "ids": [],
                "status": "success"
            }), 200
        
        # Get all JSON files in storage directory
        json_files = [f for f in os.listdir(STORAGE_DIR) if f.endswith('.json')]
        ids = [f.replace('.json', '') for f in json_files]
        
        return jsonify({
            "message": f"Found {len(ids)} stored JSON files",
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "message": "Server is running",
        "status": "healthy"
    }), 200

if __name__ == '__main__':
    logger.info("Starting JSON storage server...")
    logger.info(f"Storage directory: {os.path.abspath(STORAGE_DIR)}")
    app.run(debug=True, host='0.0.0.0', port=8080)
