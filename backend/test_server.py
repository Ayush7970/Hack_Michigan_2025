#!/usr/bin/env python3
"""
Test script for the JSON storage server
"""

import requests
import json
import time

# Server configuration
BASE_URL = "http://localhost:8080"

def test_store_json():
    """Test storing JSON data"""
    print("Testing JSON storage...")
    
    # Test data
    test_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "hobbies": ["reading", "coding", "hiking"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/store",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Successfully stored JSON data!")
            print(f"   ID: {result['id']}")
            print(f"   Message: {result['message']}")
            return result['id']
        else:
            print(f"❌ Failed to store JSON data: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running!")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_retrieve_json(unique_id):
    """Test retrieving JSON data by ID"""
    print(f"\nTesting JSON retrieval for ID: {unique_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/retrieve/{unique_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Successfully retrieved JSON data!")
            print(f"   Data: {json.dumps(result['data'], indent=2)}")
        else:
            print(f"❌ Failed to retrieve JSON data: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_list_data():
    """Test listing all stored data"""
    print("\nTesting data listing...")
    
    try:
        response = requests.get(f"{BASE_URL}/list")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Successfully listed stored data!")
            print(f"   Found {len(result['ids'])} stored files")
            print(f"   IDs: {result['ids']}")
        else:
            print(f"❌ Failed to list data: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_match_uagent():
    """Test uagent matching functionality"""
    print("\nTesting uagent matching...")
    
    # First, let's store some sample uagents
    uagents = [
        {
            "name": "Alice Johnson",
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "job": "Software Developer",
            "averagePrice": 50.0,
            "tags": ["python", "web development", "api"],
            "location": ["San Francisco", "CA"],
            "description": "I specialize in Python web development and API design. I can help with Flask, Django, and RESTful services."
        },
        {
            "name": "Bob Smith",
            "address": "0xabcdef1234567890abcdef1234567890abcdef12",
            "job": "Data Scientist",
            "averagePrice": 75.0,
            "tags": ["machine learning", "python", "data analysis"],
            "location": ["New York", "NY"],
            "description": "Expert in machine learning and data analysis using Python, pandas, scikit-learn, and TensorFlow."
        },
        {
            "name": "Carol Davis",
            "address": "0x9876543210fedcba9876543210fedcba98765432",
            "job": "Mobile Developer",
            "averagePrice": 60.0,
            "tags": ["react native", "ios", "android"],
            "location": ["Austin", "TX"],
            "description": "Mobile app developer specializing in React Native, iOS, and Android development."
        }
    ]
    
    # Store the uagents
    stored_ids = []
    for uagent in uagents:
        try:
            response = requests.post(
                f"{BASE_URL}/store",
                json=uagent,
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 201:
                result = response.json()
                stored_ids.append(result['id'])
                print(f"   ✅ Stored uagent: {uagent['name']}")
            else:
                print(f"   ❌ Failed to store uagent: {uagent['name']}")
        except Exception as e:
            print(f"   ❌ Error storing uagent: {str(e)}")
    
    # Test matching
    test_requests = [
        {
            "description": "I need help with Python web development and API design",
            "expected_match": "Alice Johnson"
        },
        {
            "description": "Looking for machine learning expertise and data analysis",
            "expected_match": "Bob Smith"
        },
        {
            "description": "Need mobile app development for iOS and Android",
            "expected_match": "Carol Davis"
        },
        {
            "description": "Help with web development and data science",
            "expected_match": "Alice Johnson"  # Should match Alice due to web development
        }
    ]
    
    for i, test_request in enumerate(test_requests, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/match",
                json={"description": test_request["description"]},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                matched_name = result['matched_uagent']['name']
                match_score = result['match_score']
                matched_address = result['matched_address']
                
                print(f"   ✅ Test {i}: Found match!")
                print(f"      Description: {test_request['description'][:50]}...")
                print(f"      Matched: {matched_name}")
                print(f"      Address: {matched_address}")
                print(f"      Score: {match_score}")
                
                if matched_name == test_request["expected_match"]:
                    print(f"      ✅ Correct match!")
                else:
                    print(f"      ⚠️  Expected {test_request['expected_match']}, got {matched_name}")
            else:
                print(f"   ❌ Test {i} failed: {response.status_code}")
                print(f"      Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Test {i} error: {str(e)}")

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Server is healthy!")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Starting JSON Storage Server Tests")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    
    # Test storing JSON data
    unique_id = test_store_json()
    
    if unique_id:
        # Test retrieving the stored data
        test_retrieve_json(unique_id)
        
        # Test listing all data
        test_list_data()
    
    # Test uagent matching functionality
    test_match_uagent()
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main()
