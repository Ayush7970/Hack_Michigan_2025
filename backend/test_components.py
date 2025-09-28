#!/usr/bin/env python3
"""
Test individual components of the server
"""

import sys
import os

def test_imports():
    """Test if all imports work"""
    print("🧪 Testing imports...")
    
    try:
        from flask import Flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        from mock_dynamodb_service import MockDynamoDBService
        print("✅ MockDynamoDBService imported successfully")
    except ImportError as e:
        print(f"❌ MockDynamoDBService import failed: {e}")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer imported successfully")
    except ImportError as e:
        print(f"❌ SentenceTransformer import failed: {e}")
        return False
    
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        print("✅ sklearn imported successfully")
    except ImportError as e:
        print(f"❌ sklearn import failed: {e}")
        return False
    
    try:
        import boto3
        print("✅ boto3 imported successfully")
    except ImportError as e:
        print(f"❌ boto3 import failed: {e}")
        return False
    
    return True

def test_mock_dynamodb():
    """Test mock DynamoDB service"""
    print("\n🧪 Testing Mock DynamoDB service...")
    
    try:
        from mock_dynamodb_service import MockDynamoDBService
        
        # Initialize service
        service = MockDynamoDBService()
        print("✅ MockDynamoDBService initialized")
        
        # Test profile storage
        test_profile = {
            "name": "Test Agent",
            "address": "test_address_123",
            "job": "Software Developer",
            "averagePrice": 75.0,
            "tags": ["python", "testing"],
            "location": ["Test City", "TS"],
            "description": "Test agent for component testing"
        }
        
        profile_id = service.store_profile(test_profile)
        print(f"✅ Profile stored with ID: {profile_id}")
        
        # Test profile retrieval
        retrieved = service.retrieve_profile(profile_id)
        if retrieved and retrieved['data']['name'] == "Test Agent":
            print("✅ Profile retrieved successfully")
        else:
            print("❌ Profile retrieval failed")
            return False
        
        # Test conversation storage
        conv_id = service.store_conversation(profile_id, "Hello!", "user")
        print(f"✅ Conversation stored with ID: {conv_id}")
        
        # Test conversation retrieval
        messages = service.get_conversation(conv_id)
        if messages and len(messages) == 1:
            print("✅ Conversation retrieved successfully")
        else:
            print("❌ Conversation retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mock DynamoDB test failed: {e}")
        return False

def test_semantic_model():
    """Test semantic model loading"""
    print("\n🧪 Testing semantic model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Try to load the model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Semantic model loaded successfully")
        
        # Test encoding
        embeddings = model.encode(["test sentence"])
        if len(embeddings) == 1 and len(embeddings[0]) > 0:
            print("✅ Model encoding works")
        else:
            print("❌ Model encoding failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Semantic model test failed: {e}")
        return False

def test_server_creation():
    """Test server creation without running it"""
    print("\n🧪 Testing server creation...")
    
    try:
        # Import server components
        from flask import Flask
        from mock_dynamodb_service import MockDynamoDBService
        
        # Create a simple Flask app
        app = Flask(__name__)
        
        # Add a simple route
        @app.route('/test')
        def test_route():
            return {"message": "test successful"}
        
        print("✅ Flask app created successfully")
        
        # Test DynamoDB service
        service = MockDynamoDBService()
        print("✅ DynamoDB service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Server creation test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Component Testing for Agent Matching System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_mock_dynamodb,
        test_semantic_model,
        test_server_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
