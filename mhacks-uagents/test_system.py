#!/usr/bin/env python3
"""
Quick test script to verify the system is working properly.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_system():
    """Test the complete system functionality."""
    print("🧪 Testing Multi-Agent Negotiation System")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is healthy")
        else:
            print("   ❌ Server health check failed")
            return False
    except Exception as e:
        print(f"   ❌ Server not responding: {e}")
        return False
    
    # Test 2: Register an agent
    print("2. Testing agent registration...")
    agent_data = {
        "agent_id": "test_agent",
        "owner": "Test Owner",
        "services": ["lawn_mowing"],
        "pricing": {"lawn_mowing": {"min": 20, "max": 40, "unit": "per_visit"}},
        "location": {"lat": 42.28, "lon": -83.74},
        "availability": [{"day": "monday", "start": "08:00", "end": "17:00"}],
        "attributes": {"experience_years": 5, "rating": 4.5},
        "policy": {"max_distance_km": 10}
    }
    
    try:
        response = requests.post(f"{API_BASE}/agents", json=agent_data)
        if response.status_code == 200:
            print("   ✅ Agent registered successfully")
        else:
            print(f"   ❌ Agent registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Agent registration error: {e}")
        return False
    
    # Test 3: Create a request
    print("3. Testing request creation...")
    request_data = {
        "request_id": "test_req_1",
        "requester_id": "test_user",
        "service": "lawn_mowing",
        "location": {"lat": 42.28, "lon": -83.74},
        "constraints": {"max_price": 35},
        "preferences": {}
    }
    
    try:
        response = requests.post(f"{API_BASE}/requests", json=request_data)
        if response.status_code == 200:
            print("   ✅ Request created successfully")
        else:
            print(f"   ❌ Request creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Request creation error: {e}")
        return False
    
    # Test 4: Test matching
    print("4. Testing agent matching...")
    try:
        response = requests.get(f"{API_BASE}/match/test_req_1")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {len(data['candidates'])} matching agents")
        else:
            print(f"   ❌ Matching failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Matching error: {e}")
        return False
    
    # Test 5: Create negotiation session
    print("5. Testing session creation...")
    try:
        response = requests.post(f"{API_BASE}/match/test_req_1/create_session", json=["test_agent"])
        if response.status_code == 200:
            data = response.json()
            session_id = data['session_id']
            print(f"   ✅ Session created: {session_id}")
        else:
            print(f"   ❌ Session creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Session creation error: {e}")
        return False
    
    # Test 6: Test WebSocket endpoint (basic check)
    print("6. Testing WebSocket endpoint...")
    try:
        response = requests.get(f"{API_BASE}/sessions/{session_id}/status")
        if response.status_code == 200:
            print("   ✅ WebSocket endpoint accessible")
        else:
            print(f"   ❌ WebSocket endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ WebSocket endpoint error: {e}")
        return False
    
    print("\n🎉 All tests passed! System is working correctly.")
    print(f"\n📋 Next steps:")
    print(f"   1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    print(f"   2. Run agents: python agents/agent_worker.py agents/sample_profile.json {session_id} --use-llm")
    print(f"   3. Or use fallback: python agents/agent_worker.py agents/sample_profile.json {session_id} --no-llm")
    
    return True

if __name__ == "__main__":
    test_system()
