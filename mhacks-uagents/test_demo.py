#!/usr/bin/env python3
"""
Demo script for the Multi-Agent Negotiation System
This script demonstrates the complete flow from agent registration to contract formation.
"""

import requests
import json
import time
import subprocess
import sys
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def make_request(method, url, data=None):
    """Make HTTP request with error handling."""
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def register_agents():
    """Register sample agents."""
    print("🤖 Registering agents...")
    
    agent_files = [
        "agents/sample_profile.json",
        "agents/another_profile.json", 
        "agents/contractor_profile.json"
    ]
    
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            with open(agent_file, 'r') as f:
                agent_data = json.load(f)
            
            result = make_request("POST", f"{API_BASE}/agents", agent_data)
            if result:
                print(f"✅ Registered agent: {agent_data['agent_id']}")
            else:
                print(f"❌ Failed to register agent: {agent_data['agent_id']}")
        else:
            print(f"⚠️  Agent file not found: {agent_file}")

def create_test_request():
    """Create a test service request."""
    print("\n📝 Creating service request...")
    
    request_data = {
        "request_id": "demo-req-1",
        "requester_id": "demo-user",
        "service": "lawn_mowing",
        "location": {"lat": 42.28, "lon": -83.74},
        "constraints": {"max_price": 45},
        "preferences": {"eco_friendly": True}
    }
    
    result = make_request("POST", f"{API_BASE}/requests", request_data)
    if result:
        print("✅ Service request created")
        return True
    else:
        print("❌ Failed to create service request")
        return False

def find_matching_agents():
    """Find agents that match the request."""
    print("\n🔍 Finding matching agents...")
    
    result = make_request("GET", f"{API_BASE}/match/demo-req-1")
    if result:
        print(f"✅ Found {len(result['candidates'])} matching agents:")
        for candidate in result['candidates']:
            print(f"   - {candidate['agent_id']} (score: {candidate['score']:.1f})")
        return result['candidates']
    else:
        print("❌ Failed to find matching agents")
        return []

def create_negotiation_session(candidates):
    """Create a negotiation session with the top candidates."""
    print("\n🤝 Creating negotiation session...")
    
    # Use top 2 candidates
    agent_ids = [candidate['agent_id'] for candidate in candidates[:2]]
    
    result = make_request("POST", f"{API_BASE}/match/demo-req-1/create_session", agent_ids)
    if result:
        session_id = result['session_id']
        print(f"✅ Negotiation session created: {session_id}")
        print(f"   WebSocket URL: {result['websocket_url']}")
        return session_id
    else:
        print("❌ Failed to create negotiation session")
        return None

def start_agent_workers(session_id):
    """Start agent workers for the negotiation."""
    print(f"\n🚀 Starting agent workers for session: {session_id}")
    
    # This would typically be done in separate terminals
    print("To start agent workers, run these commands in separate terminals:")
    print(f"   Terminal 1: python agents/agent_worker.py agents/sample_profile.json {session_id}")
    print(f"   Terminal 2: python agents/agent_worker.py agents/another_profile.json {session_id}")
    
    # For demo purposes, we'll just show the commands
    return True

def monitor_session(session_id):
    """Monitor the negotiation session."""
    print(f"\n👀 Monitoring session: {session_id}")
    
    for i in range(10):  # Check for 10 iterations
        result = make_request("GET", f"{API_BASE}/sessions/{session_id}")
        if result:
            print(f"   Status: {result['status']}, Active connections: {result['active_connections']}, Log entries: {result['log_count']}")
            
            if result['status'] == 'completed':
                print("🎉 Negotiation completed!")
                return True
        else:
            print("❌ Failed to get session status")
        
        time.sleep(2)
    
    print("⏰ Session monitoring timeout")
    return False

def check_contracts(session_id):
    """Check for finalized contracts."""
    print(f"\n📋 Checking contracts for session: {session_id}")
    
    result = make_request("GET", f"{API_BASE}/contracts/{session_id}")
    if result:
        print("✅ Contract found:")
        print(json.dumps(result['contract'], indent=2))
        return True
    else:
        print("❌ No contract found")
        return False

def main():
    """Run the complete demo."""
    print("🎯 Multi-Agent Negotiation System Demo")
    print("=" * 50)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding properly")
            return
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start it with:")
        print("   cd backend && uvicorn app.main:app --reload")
        return
    
    # Run demo steps
    register_agents()
    
    if not create_test_request():
        return
    
    candidates = find_matching_agents()
    if not candidates:
        return
    
    session_id = create_negotiation_session(candidates)
    if not session_id:
        return
    
    start_agent_workers(session_id)
    
    print("\n⏳ Waiting for agents to connect and negotiate...")
    print("   (In a real scenario, you would start the agent workers now)")
    
    # For demo purposes, we'll just show what would happen
    print("\n📊 Demo completed! Here's what would happen next:")
    print("1. Agents would connect to the WebSocket")
    print("2. They would exchange offers and counter-offers")
    print("3. When an agreement is reached, a contract would be saved")
    print("4. All participants would be notified of the final contract")
    
    print(f"\n🔗 To test manually:")
    print(f"   - API Docs: {BASE_URL}/docs")
    print(f"   - WebSocket: ws://localhost:8000/ws/session/{session_id}")
    print(f"   - Session status: {API_BASE}/sessions/{session_id}/status")

if __name__ == "__main__":
    main()
