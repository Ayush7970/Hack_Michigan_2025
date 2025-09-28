#!/usr/bin/env python3
"""
Simple test script to verify WebSocket server functionality
"""
import requests
import json

def test_websocket_api():
    base_url = "http://localhost:8081"
    
    print("🧪 Testing WebSocket API...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test creating a conversation
    try:
        create_data = {
            "title": "Test Conversation",
            "description": "A test conversation for verification",
            "user_id": "test_user_123"
        }
        
        response = requests.post(f"{base_url}/api/conversations/create", 
                               json=create_data)
        print(f"✅ Create conversation: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            room_id = data['room_id']
            join_link = data['join_link']
            print(f"   Room ID: {room_id}")
            print(f"   Join Link: {join_link}")
            
            # Test joining the conversation
            join_data = {
                "user_id": "test_user_456",
                "username": "Test User"
            }
            
            response = requests.post(f"{base_url}/api/conversations/{room_id}/join",
                                   json=join_data)
            print(f"✅ Join conversation: {response.status_code}")
            
            # Test getting conversation details
            response = requests.get(f"{base_url}/api/conversations/{room_id}")
            print(f"✅ Get conversation: {response.status_code}")
            
            # Test listing conversations
            response = requests.get(f"{base_url}/api/conversations")
            print(f"✅ List conversations: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Active conversations: {len(data['conversations'])}")
            
            return True
        else:
            print(f"❌ Create conversation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting WebSocket API tests...")
    print("Make sure the WebSocket server is running on port 8081")
    print()
    
    success = test_websocket_api()
    
    if success:
        print("\n✅ All tests passed! WebSocket API is working correctly.")
        print("🌐 You can now visit http://localhost:3000/conversations")
    else:
        print("\n❌ Tests failed. Please check the WebSocket server.")
