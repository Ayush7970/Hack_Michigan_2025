#!/usr/bin/env python3
"""
Simple server test to verify the setup works
"""

import requests
import time
import subprocess
import sys
import os

def start_server():
    """Start the server in background"""
    print("🚀 Starting server...")
    
    # Start server in background
    process = subprocess.Popen([
        sys.executable, 'server.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(5)
    
    return process

def test_endpoints():
    """Test the server endpoints"""
    print("🧪 Testing server endpoints...")
    
    base_url = "http://127.0.0.1:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test list endpoint
    try:
        response = requests.get(f"{base_url}/list", timeout=5)
        if response.status_code == 200:
            print("✅ List endpoint working")
            data = response.json()
            print(f"   Found {len(data.get('ids', []))} profiles")
        else:
            print(f"❌ List endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ List endpoint error: {e}")
        return False
    
    # Test store endpoint
    try:
        test_profile = {
            "name": "Test Agent",
            "address": "test_address_123",
            "job": "Software Developer",
            "averagePrice": 75.0,
            "tags": ["python", "testing"],
            "location": ["Test City", "TS"],
            "description": "Test agent for API testing"
        }
        
        response = requests.post(f"{base_url}/store", json=test_profile, timeout=5)
        if response.status_code == 201:
            print("✅ Store endpoint working")
            data = response.json()
            profile_id = data.get('id')
            print(f"   Profile stored with ID: {profile_id}")
        else:
            print(f"❌ Store endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Store endpoint error: {e}")
        return False
    
    # Test conversation endpoint
    try:
        conversation_data = {
            "agent_id": profile_id,
            "message": "Hello! I need help with Python development.",
            "sender": "user"
        }
        
        response = requests.post(f"{base_url}/conversation", json=conversation_data, timeout=5)
        if response.status_code == 201:
            print("✅ Conversation endpoint working")
            data = response.json()
            conv_id = data.get('conversation_id')
            print(f"   Conversation stored with ID: {conv_id}")
        else:
            print(f"❌ Conversation endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Conversation endpoint error: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Simple Server Test")
    print("=" * 30)
    
    # Start server
    server_process = start_server()
    
    try:
        # Test endpoints
        if test_endpoints():
            print("\n🎉 All tests passed! Server is working correctly.")
            print("\nYour DynamoDB migration is complete and working!")
            print("\nNext steps:")
            print("1. The server is running on http://localhost:8080")
            print("2. You can test the API endpoints")
            print("3. Check the mock_dynamodb_storage directory for your data")
        else:
            print("\n❌ Some tests failed. Check the errors above.")
    
    finally:
        # Clean up
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
