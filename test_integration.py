#!/usr/bin/env python3
"""
Test script to verify the integrated live conversation functionality
"""
import requests
import json
import time

def test_integration():
    print("🧪 Testing Integrated Live Conversation System...")
    
    # Test WebSocket server health
    try:
        response = requests.get("http://localhost:8081/api/health")
        print(f"✅ WebSocket server health: {response.status_code}")
        health_data = response.json()
        print(f"   Active conversations: {health_data['active_conversations']}")
    except Exception as e:
        print(f"❌ WebSocket server not accessible: {e}")
        return False
    
    # Test creating a live conversation
    try:
        create_data = {
            "title": "Test Live Negotiation - Plumber",
            "description": "Live conversation for plumber service negotiation",
            "user_id": "test_book_user"
        }
        
        response = requests.post("http://localhost:8081/api/conversations/create", json=create_data)
        print(f"✅ Create live conversation: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            room_id = data['room_id']
            join_link = data['join_link']
            print(f"   Room ID: {room_id}")
            print(f"   Join Link: {join_link}")
            
            # Test joining the conversation
            join_data = {
                "user_id": "test_viewer",
                "username": "Test Viewer"
            }
            
            response = requests.post(f"http://localhost:8081/api/conversations/{room_id}/join", json=join_data)
            print(f"✅ Join live conversation: {response.status_code}")
            
            return True
        else:
            print(f"❌ Create conversation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_frontend_access():
    print("\n🌐 Testing Frontend Access...")
    
    try:
        # Test main page
        response = requests.get("http://localhost:3000")
        print(f"✅ Main page: {response.status_code}")
        
        # Test book page
        response = requests.get("http://localhost:3000/book")
        print(f"✅ Book page: {response.status_code}")
        
        # Test conversations page
        response = requests.get("http://localhost:3000/conversations")
        print(f"✅ Conversations page: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend access failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Integration Tests...")
    print("Make sure both servers are running:")
    print("- WebSocket server on port 8081")
    print("- Frontend on port 3000")
    print()
    
    websocket_success = test_integration()
    frontend_success = test_frontend_access()
    
    print("\n" + "="*50)
    if websocket_success and frontend_success:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Live conversation integration is working!")
        print("\n📋 How to test the integration:")
        print("1. Go to http://localhost:3000/book")
        print("2. Enter a service request (e.g., 'I need a plumber')")
        print("3. Click 'Find' and continue through the flow")
        print("4. On the negotiation page, click 'Create Live Conversation'")
        print("5. Copy the generated link and share it")
        print("6. Open the link in another browser tab to test real-time chat")
    else:
        print("❌ Some tests failed. Please check the servers.")
        if not websocket_success:
            print("   - WebSocket server issue")
        if not frontend_success:
            print("   - Frontend server issue")
