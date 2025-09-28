"""
Simple but effective agent-to-agent negotiation with Gemini completion detection
Avoids complex async messaging issues by using direct function calls
"""

import os
import json
import time
from typing import Dict, List, Any
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("🤖 Gemini AI loaded successfully")
else:
    model = None
    print("⚠️ No Gemini API key - using basic completion detection")

# Create conversations directory
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# Global storage
conversations: Dict[str, Dict[str, Any]] = {}

def save_conversation(conversation_id: str, conversation_data: Dict):
    """Save conversation to local file"""
    try:
        filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
        with open(filepath, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        print(f"💾 Saved conversation {conversation_id}")
    except Exception as e:
        print(f"❌ Error saving conversation {conversation_id}: {e}")

def load_conversation(conversation_id: str) -> Dict:
    """Load conversation from local file"""
    try:
        filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        return {}
    except Exception as e:
        print(f"❌ Error loading conversation {conversation_id}: {e}")
        return {}

def check_negotiation_status_with_gemini(conversation_history: List[Dict]) -> str:
    """Use Gemini to determine if negotiation is complete"""

    if not model or len(conversation_history) < 2:
        return "CONTINUE"

    # Get recent messages
    recent_messages = conversation_history[-4:] if len(conversation_history) >= 4 else conversation_history

    history_text = ""
    for msg in recent_messages:
        role = "Customer" if msg["from"] == "buyer" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    analysis_prompt = f"""
Analyze this negotiation conversation and determine if it's COMPLETE or should CONTINUE.

A negotiation is COMPLETE when:
- Both parties have clearly agreed on price and terms
- Someone confirms booking/scheduling the service
- Clear acceptance like "deal", "sounds good", "let's do it", "perfect"
- Agreement on when/how the service will happen

A negotiation should CONTINUE when:
- Still discussing price or terms
- Asking questions about the service
- Negotiating details
- No clear agreement yet

Conversation:
{history_text}

Respond with ONLY "COMPLETE" or "CONTINUE" - nothing else.
"""

    try:
        response = model.generate_content(analysis_prompt)
        result = response.text.strip().upper()

        print(f"🧠 Gemini status check: {result}")

        if "COMPLETE" in result:
            return "COMPLETE"
        else:
            return "CONTINUE"

    except Exception as e:
        print(f"❌ Gemini analysis error: {e}")
        # Fallback to keyword detection
        recent_text = " ".join([msg["content"].lower() for msg in recent_messages])
        complete_keywords = ['deal', 'agreed', 'book', 'schedule', 'sounds good', 'perfect', 'let\'s do it', 'yes that works']
        if any(keyword in recent_text for keyword in complete_keywords):
            return "COMPLETE"
        return "CONTINUE"

def generate_buyer_response(conversation_history: List[Dict], user_request: str) -> str:
    """Generate buyer response using Gemini"""

    history_text = ""
    for msg in conversation_history:
        role = "You" if msg["from"] == "buyer" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are a customer who originally requested: {user_request}

Conversation so far:
{history_text}

Continue the negotiation by responding to the service provider's latest message. You should:
- Negotiate price and terms professionally
- Ask clarifying questions if needed
- Show interest but protect your budget
- Move toward agreement if the offer is reasonable
- Accept good deals when offered

Respond in under 50 words. Be natural and conversational.
"""

    if model:
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Buyer Gemini error: {e}")

    # Fallback response
    return "That sounds interesting. Can you tell me more about the pricing and what's included in the service?"

def generate_provider_response(agent_profile: Dict, conversation_history: List[Dict]) -> str:
    """Generate provider response using Gemini"""

    history_text = ""
    for msg in conversation_history:
        role = "Customer" if msg["from"] == "buyer" else "You"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are {agent_profile.get('name', 'a service provider')} - {agent_profile.get('job', 'a professional')}.
Your average price is ${agent_profile.get('averagePrice', 50)}/hr.
Description: {agent_profile.get('description', 'I provide quality services')}

Conversation so far:
{history_text}

Continue the negotiation by responding to the customer's latest message. You should:
- Provide helpful information about your services
- Negotiate price fairly but protect your value
- Be professional and friendly
- Work toward closing the deal when appropriate
- Explain your expertise and value

Respond in under 50 words. Be natural and conversational.
"""

    if model:
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Provider Gemini error: {e}")

    # Fallback response
    avg_price = agent_profile.get('averagePrice', 50)
    return f"I typically charge ${avg_price}/hr for this type of work. I have experience with similar projects and can deliver quality results. Would that work for your budget?"

def run_negotiation_turn(conversation_id: str, max_turns: int = 10) -> bool:
    """Run one complete turn of negotiation (provider response + buyer response)"""

    conv = load_conversation(conversation_id)
    if not conv:
        print(f"❌ No conversation found: {conversation_id}")
        return False

    if conv.get("is_complete", False):
        print(f"✅ Negotiation {conversation_id} already complete")
        return True

    turn_count = len(conv.get("messages", []))

    if turn_count >= max_turns:
        print(f"🛑 Max turns reached for {conversation_id}")
        conv["is_complete"] = True
        conv["completion_reason"] = "max_turns_reached"
        save_conversation(conversation_id, conv)
        return True

    print(f"🔄 Running turn {turn_count + 1} for {conversation_id}")

    # Provider responds to latest buyer message
    provider_response = generate_provider_response(conv["agent_profile"], conv["messages"])
    print(f"🔧 Provider: {provider_response}")

    conv["messages"].append({
        "from": "provider",
        "content": provider_response,
        "timestamp": time.time(),
        "turn": turn_count + 1
    })

    # Check if complete after provider response
    status = check_negotiation_status_with_gemini(conv["messages"])
    if status == "COMPLETE":
        print(f"🏁 Negotiation {conversation_id} completed after provider response!")
        conv["is_complete"] = True
        conv["completion_reason"] = "agreement_reached"
        save_conversation(conversation_id, conv)
        return True

    # Buyer responds to provider
    buyer_response = generate_buyer_response(conv["messages"], conv["user_request"])
    print(f"🛒 Buyer: {buyer_response}")

    conv["messages"].append({
        "from": "buyer",
        "content": buyer_response,
        "timestamp": time.time(),
        "turn": turn_count + 2
    })

    # Check if complete after buyer response
    status = check_negotiation_status_with_gemini(conv["messages"])
    if status == "COMPLETE":
        print(f"🏁 Negotiation {conversation_id} completed after buyer response!")
        conv["is_complete"] = True
        conv["completion_reason"] = "agreement_reached"
        save_conversation(conversation_id, conv)
        return True

    # Save and continue
    save_conversation(conversation_id, conv)
    return False

def run_full_negotiation(conversation_id: str, max_turns: int = 20):
    """Run the full negotiation until completion"""

    print(f"🚀 Starting full negotiation for {conversation_id}")

    try:
        for i in range(max_turns // 2):  # Each turn is 2 messages
            print(f"🔄 Turn {i + 1}/{max_turns // 2}")
            is_complete = run_negotiation_turn(conversation_id, max_turns)
            if is_complete:
                print(f"✅ Negotiation completed at turn {i + 1}")
                break
            time.sleep(0.1)  # Small delay between turns

        print(f"🏁 Negotiation finished for {conversation_id}")

    except Exception as e:
        print(f"❌ Error in run_full_negotiation: {e}")
        import traceback
        print(f"📍 Full traceback: {traceback.format_exc()}")

        # Mark conversation as error
        conv = load_conversation(conversation_id)
        if conv:
            conv["is_complete"] = True
            conv["completion_reason"] = f"error: {str(e)}"
            save_conversation(conversation_id, conv)

# Flask API
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

@app.route('/negotiate', methods=['POST'])
def negotiate():
    """Start negotiation and run it to completion"""
    try:
        print("🔥 Negotiate endpoint called")

        data = request.get_json()
        print(f"📦 Received data: {data}")

        if not data:
            print("❌ No JSON data received")
            return jsonify({"error": "No JSON data provided"}), 400

        conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
        user_message = data.get('message', '')
        agent_profile = data.get('agent_profile', {})

        print(f"🔥 Parsed - ID: {conversation_id}")
        print(f"📨 Message: {user_message}")
        print(f"🤖 Profile: {agent_profile}")

        if not user_message:
            print("❌ No user message provided")
            return jsonify({"error": "No message provided"}), 400

        print(f"✅ Starting negotiation: {conversation_id}")

        # Create new conversation
        conv = {
            "conversation_id": conversation_id,
            "messages": [{
                "from": "buyer",
                "content": user_message,
                "timestamp": time.time(),
                "turn": 1
            }],
            "agent_profile": agent_profile,
            "user_request": user_message,
            "is_complete": False,
            "created_at": time.time()
        }

        print("💾 Saving initial conversation...")
        save_conversation(conversation_id, conv)

        print("🚀 Running full negotiation...")
        run_full_negotiation(conversation_id)

        print("📁 Loading final conversation...")
        final_conv = load_conversation(conversation_id)

        result = {
            "success": True,
            "conversation_id": conversation_id,
            "is_complete": final_conv.get("is_complete", False),
            "message_count": len(final_conv.get("messages", [])),
            "completion_reason": final_conv.get("completion_reason", "ongoing")
        }

        print(f"✅ Returning result: {result}")
        return jsonify(result)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ FULL ERROR in negotiate: {e}")
        print(f"📍 TRACEBACK: {error_trace}")
        return jsonify({"error": str(e), "traceback": error_trace}), 500

@app.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        conv = load_conversation(conversation_id)

        if not conv:
            return jsonify({
                "messages": [],
                "is_complete": False,
                "agent_profile": {}
            })

        # Format messages for frontend
        formatted_messages = []
        for msg in conv.get("messages", []):
            formatted_messages.append({
                "role": "user" if msg["from"] == "buyer" else "agent",
                "content": msg["content"],
                "timestamp": msg.get("timestamp", time.time())
            })

        return jsonify({
            "messages": formatted_messages,
            "is_complete": conv.get("is_complete", False),
            "agent_profile": conv.get("agent_profile", {}),
            "completion_reason": conv.get("completion_reason", None)
        })

    except Exception as e:
        print(f"❌ Error getting conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Simple test endpoint"""
    try:
        data = request.get_json()
        print(f"🧪 Test endpoint received: {data}")

        return jsonify({
            "success": True,
            "message": "Test endpoint working",
            "received_data": data,
            "ai_available": model is not None
        })

    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    try:
        conv_files = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith('.json')]
        total_conversations = len(conv_files)
    except:
        total_conversations = 0

    return jsonify({
        "status": "healthy",
        "total_conversations": total_conversations,
        "ai_available": model is not None,
        "conversations_dir": CONVERSATIONS_DIR
    })

if __name__ == "__main__":
    print("🚀 Starting Simple Agent Negotiation System")
    print(f"🤖 AI Model: {'Gemini Available' if model else 'Basic responses only'}")
    print(f"💾 Conversations saved to: {os.path.abspath(CONVERSATIONS_DIR)}")
    print("🌐 API available at http://localhost:8001")

    app.run(debug=True, host='0.0.0.0', port=8001)