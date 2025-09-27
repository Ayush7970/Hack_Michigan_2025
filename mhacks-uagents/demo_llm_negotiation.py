#!/usr/bin/env python3
"""
Enhanced demo script showcasing LLM-powered negotiation system.
This demonstrates intelligent agent negotiation with reasoning and strategic decision making.
"""

import requests
import json
import time
import subprocess
import sys
import os
import asyncio
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

def setup_environment():
    """Set up the environment for LLM negotiation."""
    print("🔧 Setting up LLM negotiation environment...")
    
    # Check for Gemini API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  No GEMINI_API_KEY found in environment variables")
        print("   Set your API key with: export GEMINI_API_KEY='your-key-here'")
        print("   Or the system will fall back to rule-based negotiation")
        return False
    
    print("✅ Gemini API key found")
    return True

def register_enhanced_agents():
    """Register agents with enhanced profiles for better negotiation."""
    print("🤖 Registering enhanced agents...")
    
    # Enhanced agent profiles with more detailed negotiation preferences
    enhanced_profiles = [
        {
            "agent_id": "premium_lawn_care",
            "owner": "Premium Lawn Care Services",
            "services": ["lawn_mowing", "hedge_trimming", "garden_maintenance"],
            "pricing": {
                "lawn_mowing": {"min": 30, "max": 60, "unit": "per_visit"},
                "hedge_trimming": {"min": 40, "max": 80, "unit": "per_visit"},
                "garden_maintenance": {"min": 50, "max": 100, "unit": "per_visit"}
            },
            "location": {"lat": 42.2808, "lon": -83.7430},
            "availability": [
                {"day": "monday", "start": "08:00", "end": "17:00"},
                {"day": "tuesday", "start": "08:00", "end": "17:00"},
                {"day": "wednesday", "start": "08:00", "end": "17:00"},
                {"day": "thursday", "start": "08:00", "end": "17:00"},
                {"day": "friday", "start": "08:00", "end": "17:00"}
            ],
            "attributes": {
                "experience_years": 8,
                "rating": 4.9,
                "equipment": ["professional_mower", "hedge_trimmer", "leaf_blower"],
                "insurance": True,
                "licensed": True,
                "premium_service": True
            },
            "policy": {
                "max_distance_km": 15,
                "min_notice_hours": 24,
                "payment_terms": "card_preferred",
                "guarantee_days": 14,
                "negotiation_style": "collaborative",
                "key_priorities": ["quality", "reliability", "customer_satisfaction"]
            }
        },
        {
            "agent_id": "eco_friendly_gardener",
            "owner": "Eco-Friendly Garden Solutions",
            "services": ["lawn_mowing", "garden_maintenance", "landscaping"],
            "pricing": {
                "lawn_mowing": {"min": 25, "max": 50, "unit": "per_visit"},
                "garden_maintenance": {"min": 40, "max": 75, "unit": "per_visit"},
                "landscaping": {"min": 150, "max": 400, "unit": "per_project"}
            },
            "location": {"lat": 42.2900, "lon": -83.7300},
            "availability": [
                {"day": "monday", "start": "07:00", "end": "16:00"},
                {"day": "tuesday", "start": "07:00", "end": "16:00"},
                {"day": "wednesday", "start": "07:00", "end": "16:00"},
                {"day": "thursday", "start": "07:00", "end": "16:00"},
                {"day": "friday", "start": "07:00", "end": "16:00"},
                {"day": "saturday", "start": "08:00", "end": "14:00"}
            ],
            "attributes": {
                "experience_years": 6,
                "rating": 4.8,
                "equipment": ["electric_mower", "manual_tools", "organic_fertilizers"],
                "insurance": True,
                "licensed": True,
                "eco_certified": True
            },
            "policy": {
                "max_distance_km": 20,
                "min_notice_hours": 12,
                "payment_terms": "any_method",
                "guarantee_days": 21,
                "negotiation_style": "collaborative",
                "key_priorities": ["environmental_sustainability", "organic_methods", "long_term_relationships"]
            }
        }
    ]
    
    for profile in enhanced_profiles:
        result = make_request("POST", f"{API_BASE}/agents", profile)
        if result:
            print(f"✅ Registered enhanced agent: {profile['agent_id']}")
        else:
            print(f"❌ Failed to register agent: {profile['agent_id']}")

def create_complex_request():
    """Create a more complex service request to test negotiation."""
    print("\n📝 Creating complex service request...")
    
    request_data = {
        "request_id": "complex-req-1",
        "requester_id": "premium-customer",
        "service": "lawn_mowing",
        "location": {"lat": 42.28, "lon": -83.74},
        "constraints": {
            "max_price": 55,
            "min_rating": 4.5,
            "must_be_insured": True,
            "preferred_style": "eco_friendly"
        },
        "preferences": {
            "eco_friendly": True,
            "premium_service": False,
            "flexible_timing": True,
            "long_term_relationship": True
        },
        "metadata": {
            "property_size": "medium",
            "frequency": "weekly",
            "special_requirements": "pet_safe_products_only"
        }
    }
    
    result = make_request("POST", f"{API_BASE}/requests", request_data)
    if result:
        print("✅ Complex service request created")
        return True
    else:
        print("❌ Failed to create service request")
        return False

def find_matching_agents():
    """Find agents that match the complex request."""
    print("\n🔍 Finding matching agents for complex request...")
    
    result = make_request("GET", f"{API_BASE}/match/complex-req-1")
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
    print("\n🤝 Creating LLM-powered negotiation session...")
    
    # Use top 2 candidates
    agent_ids = [candidate['agent_id'] for candidate in candidates[:2]]
    
    result = make_request("POST", f"{API_BASE}/match/complex-req-1/create_session", agent_ids)
    if result:
        session_id = result['session_id']
        print(f"✅ Negotiation session created: {session_id}")
        print(f"   WebSocket URL: {result['websocket_url']}")
        return session_id
    else:
        print("❌ Failed to create negotiation session")
        return None

def start_llm_agents(session_id):
    """Start LLM-powered agent workers."""
    print(f"\n🚀 Starting LLM-powered agent workers for session: {session_id}")
    
    print("To start LLM-powered agents, run these commands in separate terminals:")
    print(f"   Terminal 1: python agents/agent_worker.py agents/sample_profile.json {session_id} --use-llm")
    print(f"   Terminal 2: python agents/agent_worker.py agents/another_profile.json {session_id} --use-llm")
    
    print("\nOr for rule-based fallback:")
    print(f"   Terminal 1: python agents/agent_worker.py agents/sample_profile.json {session_id} --no-llm")
    print(f"   Terminal 2: python agents/agent_worker.py agents/another_profile.json {session_id} --no-llm")
    
    return True

def monitor_negotiation(session_id):
    """Monitor the negotiation session with detailed logging."""
    print(f"\n👀 Monitoring LLM negotiation session: {session_id}")
    
    for i in range(15):  # Monitor for 30 seconds
        result = make_request("GET", f"{API_BASE}/sessions/{session_id}")
        if result:
            print(f"   Status: {result['status']}, Active connections: {result['active_connections']}, Log entries: {result['log_count']}")
            
            if result['status'] == 'completed':
                print("🎉 LLM negotiation completed!")
                return True
        else:
            print("❌ Failed to get session status")
        
        time.sleep(2)
    
    print("⏰ Session monitoring timeout")
    return False

def analyze_negotiation_log(session_id):
    """Analyze the negotiation log for insights."""
    print(f"\n📊 Analyzing negotiation log for session: {session_id}")
    
    result = make_request("GET", f"{API_BASE}/sessions/{session_id}")
    if result and result.get('log'):
        print("📝 Negotiation Log Analysis:")
        print("=" * 50)
        
        for i, log_entry in enumerate(result['log'][-10:], 1):  # Show last 10 entries
            print(f"{i}. [{log_entry.get('timestamp', 'unknown')}] {log_entry.get('type', 'unknown')}")
            print(f"   From: {log_entry.get('from', 'unknown')}")
            
            if log_entry.get('reasoning'):
                print(f"   Reasoning: {log_entry['reasoning']}")
            
            if log_entry.get('confidence'):
                print(f"   Confidence: {log_entry['confidence']:.2f}")
            
            if log_entry.get('offer'):
                offer = log_entry['offer']
                print(f"   Offer: {offer.get('service', 'unknown')} - ${offer.get('price', 0)}")
            
            print()

def check_final_contracts(session_id):
    """Check for finalized contracts."""
    print(f"\n📋 Checking final contracts for session: {session_id}")
    
    result = make_request("GET", f"{API_BASE}/contracts/{session_id}")
    if result:
        print("✅ Contract found:")
        print(json.dumps(result['contract'], indent=2))
        return True
    else:
        print("❌ No contract found")
        return False

def main():
    """Run the enhanced LLM negotiation demo."""
    print("🎯 LLM-Powered Multi-Agent Negotiation System Demo")
    print("=" * 60)
    
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
    
    # Set up environment
    has_llm = setup_environment()
    
    # Run demo steps
    register_enhanced_agents()
    
    if not create_complex_request():
        return
    
    candidates = find_matching_agents()
    if not candidates:
        return
    
    session_id = create_negotiation_session(candidates)
    if not session_id:
        return
    
    start_llm_agents(session_id)
    
    print("\n⏳ Waiting for agents to connect and negotiate...")
    print("   (In a real scenario, you would start the agent workers now)")
    
    # For demo purposes, show what would happen
    print("\n📊 Enhanced Demo completed! Here's what the LLM system provides:")
    print("1. 🧠 Intelligent decision making based on agent profiles")
    print("2. 📈 Strategic negotiation tactics (aggressive, collaborative, competitive)")
    print("3. 🎯 Context-aware reasoning for each decision")
    print("4. 📊 Confidence scoring for negotiation decisions")
    print("5. 🔄 Adaptive strategies based on negotiation history")
    print("6. 💡 Detailed reasoning for each offer, counter-offer, or rejection")
    
    print(f"\n🔗 To test manually:")
    print(f"   - API Docs: {BASE_URL}/docs")
    print(f"   - WebSocket: ws://localhost:8000/ws/session/{session_id}")
    print(f"   - Session status: {API_BASE}/sessions/{session_id}/status")
    
    if has_llm:
        print(f"\n🤖 LLM Features Available:")
        print(f"   - Set GEMINI_API_KEY environment variable")
        print(f"   - Use --use-llm flag when starting agents")
        print(f"   - Agents will make intelligent, context-aware decisions")

if __name__ == "__main__":
    main()
