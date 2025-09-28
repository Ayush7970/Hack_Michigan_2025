#!/usr/bin/env python3
"""
Test script for DynamoDB functionality
"""

import requests
import json
import time

# Server configuration
SERVER_URL = "http://localhost:8080"

def test_profile_operations():
    """Test profile storage and retrieval"""
    print("🧪 Testing Profile Operations")
    print("=" * 40)
    
    # Test data
    test_profile = {
        "name": "Test Agent",
        "address": "test_address_123",
        "job": "Software Developer",
        "averagePrice": 75.0,
        "tags": ["python", "testing", "dynamodb"],
        "location": ["Test City", "TS"],
        "description": "Test agent for DynamoDB functionality testing"
    }
    
    # Test storing profile
    print("1. Testing profile storage...")
    response = requests.post(
        f"{SERVER_URL}/store",
        json=test_profile,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        result = response.json()
        profile_id = result['id']
        print(f"   ✅ Profile stored successfully with ID: {profile_id}")
    else:
        print(f"   ❌ Failed to store profile: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    # Test retrieving profile
    print("2. Testing profile retrieval...")
    response = requests.get(f"{SERVER_URL}/retrieve/{profile_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Profile retrieved successfully")
        print(f"   Name: {result['data']['data']['name']}")
        print(f"   Job: {result['data']['data']['job']}")
    else:
        print(f"   ❌ Failed to retrieve profile: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test listing profiles
    print("3. Testing profile listing...")
    response = requests.get(f"{SERVER_URL}/list")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Found {len(result['ids'])} profiles")
    else:
        print(f"   ❌ Failed to list profiles: {response.status_code}")
    
    return profile_id

def test_conversation_operations(agent_id):
    """Test conversation storage and retrieval"""
    print("\n💬 Testing Conversation Operations")
    print("=" * 40)
    
    if not agent_id:
        print("   ⚠️  Skipping conversation tests - no agent ID available")
        return
    
    # Test storing conversation
    print("1. Testing conversation storage...")
    conversation_data = {
        "agent_id": agent_id,
        "message": "Hello! I'm interested in your services.",
        "sender": "user"
    }
    
    response = requests.post(
        f"{SERVER_URL}/conversation",
        json=conversation_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        result = response.json()
        conversation_id = result['conversation_id']
        print(f"   ✅ Conversation stored successfully with ID: {conversation_id}")
    else:
        print(f"   ❌ Failed to store conversation: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    # Test storing agent response
    print("2. Testing agent response storage...")
    agent_response = {
        "agent_id": agent_id,
        "message": "Hello! I'd be happy to help you. What specific services do you need?",
        "sender": "agent",
        "conversation_id": conversation_id
    }
    
    response = requests.post(
        f"{SERVER_URL}/conversation",
        json=agent_response,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        print(f"   ✅ Agent response stored successfully")
    else:
        print(f"   ❌ Failed to store agent response: {response.status_code}")
    
    # Test retrieving conversation
    print("3. Testing conversation retrieval...")
    response = requests.get(f"{SERVER_URL}/conversation/{conversation_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Conversation retrieved successfully")
        print(f"   Messages: {len(result['messages'])}")
        for msg in result['messages']:
            print(f"   - {msg['sender']}: {msg['message']}")
    else:
        print(f"   ❌ Failed to retrieve conversation: {response.status_code}")
    
    # Test getting agent conversations
    print("4. Testing agent conversations retrieval...")
    response = requests.get(f"{SERVER_URL}/agent/{agent_id}/conversations")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Found {len(result['conversations'])} conversations for agent")
    else:
        print(f"   ❌ Failed to retrieve agent conversations: {response.status_code}")
    
    return conversation_id

def test_matching():
    """Test the matching functionality"""
    print("\n🎯 Testing Matching Operations")
    print("=" * 40)
    
    # Test matching
    print("1. Testing agent matching...")
    match_request = {
        "description": "I need help with Python development and testing"
    }
    
    response = requests.post(
        f"{SERVER_URL}/match",
        json=match_request,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Match found successfully")
        print(f"   Matched agent: {result['matched_uagent']['name']}")
        print(f"   Job: {result['matched_uagent']['job']}")
        print(f"   Match score: {result['match_score']}")
    else:
        print(f"   ❌ Failed to find match: {response.status_code}")
        print(f"   Response: {response.text}")

def test_health():
    """Test health check"""
    print("\n🏥 Testing Health Check")
    print("=" * 40)
    
    response = requests.get(f"{SERVER_URL}/health")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Server is healthy: {result['message']}")
    else:
        print(f"   ❌ Health check failed: {response.status_code}")

def main():
    """Main test function"""
    print("🚀 DynamoDB Backend Test Suite")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Test health first
    test_health()
    
    # Test profile operations
    agent_id = test_profile_operations()
    
    # Test conversation operations
    test_conversation_operations(agent_id)
    
    # Test matching
    test_matching()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\nIf all tests passed, your DynamoDB backend is working correctly!")

if __name__ == "__main__":
    main()
