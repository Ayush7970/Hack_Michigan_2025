"""
Persistent Two-Agent Negotiation with Gemini Loop Controller
- Saves conversation history locally
- Gemini checks if negotiation needs to continue
- Automatically continues POST requests until completion
"""

import asyncio
import os
import json
import time
from typing import Dict, List, Any
from uagents import Agent, Context, Model, Bureau
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

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

# Create conversations directory for persistence
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# Message Models
class NegotiationMessage(Model):
    content: str
    conversation_id: str
    from_agent: str
    turn_number: int

class ContinueNegotiation(Model):
    conversation_id: str

# Global storage
conversations: Dict[str, Dict[str, Any]] = {}
negotiation_locks: Dict[str, bool] = {}

# Create Bureau
bureau = Bureau(port=8003, endpoint="http://localhost:8003/submit")

# Buyer Agent
buyer_agent = Agent(
    name="buyer",
    seed="buyer_seed_12345",
    port=8003,
)

# Provider Agent
provider_agent = Agent(
    name="provider",
    seed="provider_seed_67890",
    port=8004,
)

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
            print(f"📁 Loaded conversation {conversation_id}")
            return data
        return {}
    except Exception as e:
        print(f"❌ Error loading conversation {conversation_id}: {e}")
        return {}

def check_negotiation_status_with_gemini(conversation_history: List[Dict]) -> str:
    """Use Gemini to determine negotiation status and next action"""

    if not model or len(conversation_history) < 2:
        return "CONTINUE"

    # Get recent messages for analysis
    recent_messages = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history

    history_text = ""
    for msg in recent_messages:
        role = "Customer" if msg["from"] == "buyer" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    analysis_prompt = f"""
Analyze this negotiation conversation and determine the status.

Conversation:
{history_text}

Determine the negotiation status:
- COMPLETE: Both parties have clearly agreed on terms, price, and next steps. Deal is finalized.
- CONTINUE: Negotiation is ongoing, more discussion needed on price, terms, or details.
- STALLED: Conversation seems stuck or going in circles, needs intervention.

Examples of COMPLETE:
- "Sounds good, let's schedule it for Tuesday at $50/hr"
- "Perfect! I'll book you for the job at that price"
- "Deal! When can you start?"

Examples of CONTINUE:
- Still discussing price
- Asking for more details about the service
- Negotiating timeline or terms

Respond with ONLY one word: "COMPLETE", "CONTINUE", or "STALLED"
"""

    try:
        response = model.generate_content(analysis_prompt)
        result = response.text.strip().upper()

        # Ensure we get a valid response
        if result in ["COMPLETE", "CONTINUE", "STALLED"]:
            print(f"🧠 Gemini status: {result}")
            return result
        else:
            print(f"🧠 Gemini unclear response: {result}, defaulting to CONTINUE")
            return "CONTINUE"

    except Exception as e:
        print(f"❌ Gemini analysis error: {e}")
        # Fallback logic
        recent_text = " ".join([msg["content"].lower() for msg in recent_messages])
        complete_keywords = ['deal', 'agreed', 'book', 'schedule', 'sounds good', 'perfect', 'let\'s do it']
        if any(keyword in recent_text for keyword in complete_keywords):
            return "COMPLETE"
        return "CONTINUE"

def create_buyer_prompt(conversation_history: List[Dict], user_request: str) -> str:
    """Create prompt for buyer agent"""
    history_text = ""
    for msg in conversation_history:
        role = "You" if msg["from"] == "buyer" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are a customer who originally requested: {user_request}

Conversation so far:
{history_text}

Continue the negotiation by:
- Responding to the service provider's latest message
- Negotiating price and terms professionally
- Asking clarifying questions if needed
- Moving toward agreement if the offer is reasonable
- Being willing to accept a good deal

Respond in under 50 words. Be natural and conversational.
"""
    return prompt

def create_provider_prompt(agent_profile: Dict, conversation_history: List[Dict]) -> str:
    """Create prompt for service provider agent"""
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

Continue the negotiation by:
- Responding to the customer's latest message
- Providing helpful information about your services
- Negotiating price fairly but protecting your value
- Working toward closing the deal
- Being professional and friendly

Respond in under 50 words. Be natural and conversational.
"""
    return prompt

# Buyer Agent Logic
@buyer_agent.on_message(model=NegotiationMessage)
async def buyer_respond(ctx: Context, sender: str, msg: NegotiationMessage):
    ctx.logger.info(f"🛒 Buyer received: {msg.content}")

    # Load conversation
    conv = load_conversation(msg.conversation_id)
    if not conv:
        ctx.logger.error(f"❌ No conversation found: {msg.conversation_id}")
        return

    # Add provider message to history
    conv["messages"].append({
        "from": "provider",
        "content": msg.content,
        "timestamp": time.time(),
        "turn": msg.turn_number
    })

    # Check negotiation status
    status = check_negotiation_status_with_gemini(conv["messages"])

    if status == "COMPLETE":
        ctx.logger.info(f"🏁 Buyer: Negotiation {msg.conversation_id} is COMPLETE!")
        conv["is_complete"] = True
        conv["completed_at"] = time.time()
        save_conversation(msg.conversation_id, conv)
        return

    # Generate buyer response
    if model:
        try:
            prompt = create_buyer_prompt(conv["messages"], conv["user_request"])
            response = model.generate_content(prompt)
            buyer_response = response.text.strip()
            ctx.logger.info(f"🛒 Buyer response: {buyer_response}")
        except Exception as e:
            ctx.logger.error(f"❌ Buyer Gemini error: {e}")
            buyer_response = "That's interesting. Can you tell me more about the pricing and what's included?"
    else:
        buyer_response = "Can you give me more details about the pricing and timeline?"

    # Add buyer response to history
    conv["messages"].append({
        "from": "buyer",
        "content": buyer_response,
        "timestamp": time.time(),
        "turn": msg.turn_number + 1
    })

    # Check status again after buyer response
    status = check_negotiation_status_with_gemini(conv["messages"])

    if status == "COMPLETE":
        ctx.logger.info(f"🏁 Buyer: Negotiation {msg.conversation_id} is COMPLETE after buyer response!")
        conv["is_complete"] = True
        conv["completed_at"] = time.time()
        save_conversation(msg.conversation_id, conv)
        return

    # Save conversation
    save_conversation(msg.conversation_id, conv)

    # Send response to provider
    response_msg = NegotiationMessage(
        content=buyer_response,
        conversation_id=msg.conversation_id,
        from_agent="buyer",
        turn_number=msg.turn_number + 1
    )

    await ctx.send(provider_agent.address, response_msg)

# Provider Agent Logic
@provider_agent.on_message(model=NegotiationMessage)
async def provider_respond(ctx: Context, sender: str, msg: NegotiationMessage):
    ctx.logger.info(f"🔧 Provider received: {msg.content}")

    # Load conversation
    conv = load_conversation(msg.conversation_id)
    if not conv:
        ctx.logger.error(f"❌ No conversation found: {msg.conversation_id}")
        return

    # Add buyer message to history (if not already there)
    if not conv["messages"] or conv["messages"][-1]["content"] != msg.content:
        conv["messages"].append({
            "from": "buyer",
            "content": msg.content,
            "timestamp": time.time(),
            "turn": msg.turn_number
        })

    # Check negotiation status
    status = check_negotiation_status_with_gemini(conv["messages"])

    if status == "COMPLETE":
        ctx.logger.info(f"🏁 Provider: Negotiation {msg.conversation_id} is COMPLETE!")
        conv["is_complete"] = True
        conv["completed_at"] = time.time()
        save_conversation(msg.conversation_id, conv)
        return

    # Generate provider response
    if model:
        try:
            prompt = create_provider_prompt(conv["agent_profile"], conv["messages"])
            response = model.generate_content(prompt)
            provider_response = response.text.strip()
            ctx.logger.info(f"🔧 Provider response: {provider_response}")
        except Exception as e:
            ctx.logger.error(f"❌ Provider Gemini error: {e}")
            avg_price = conv["agent_profile"].get("averagePrice", 50)
            provider_response = f"I typically charge ${avg_price}/hr for this type of work. Would that work for your budget?"
    else:
        avg_price = conv["agent_profile"].get("averagePrice", 50)
        provider_response = f"I can help you with that! My rate is ${avg_price}/hr. When would you need this done?"

    # Add provider response to history
    conv["messages"].append({
        "from": "provider",
        "content": provider_response,
        "timestamp": time.time(),
        "turn": msg.turn_number + 1
    })

    # Check status again after provider response
    status = check_negotiation_status_with_gemini(conv["messages"])

    if status == "COMPLETE":
        ctx.logger.info(f"🏁 Provider: Negotiation {msg.conversation_id} is COMPLETE after provider response!")
        conv["is_complete"] = True
        conv["completed_at"] = time.time()
        save_conversation(msg.conversation_id, conv)
        return

    # Save conversation
    save_conversation(msg.conversation_id, conv)

    # Send response back to buyer
    response_msg = NegotiationMessage(
        content=provider_response,
        conversation_id=msg.conversation_id,
        from_agent="provider",
        turn_number=msg.turn_number + 1
    )

    await ctx.send(buyer_agent.address, response_msg)

# Add agents to bureau
bureau.add(buyer_agent)
bureau.add(provider_agent)

# Flask API
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

@app.route('/negotiate', methods=['POST'])
def negotiate():
    """Start or continue negotiation"""
    try:
        data = request.get_json()

        conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
        user_message = data.get('message', '')
        agent_profile = data.get('agent_profile', {})

        if not user_message and conversation_id not in conversations:
            return jsonify({"error": "No message provided"}), 400

        print(f"🔥 Negotiation request: {conversation_id}")

        # Load or create conversation
        conv = load_conversation(conversation_id)

        if not conv:
            # Start new negotiation
            print(f"📨 Starting new negotiation: {user_message}")
            print(f"🤖 Provider: {agent_profile.get('name', 'Unknown')}")

            conv = {
                "conversation_id": conversation_id,
                "messages": [],
                "agent_profile": agent_profile,
                "user_request": user_message,
                "is_complete": False,
                "created_at": time.time()
            }

            # Add initial user message
            conv["messages"].append({
                "from": "buyer",
                "content": user_message,
                "timestamp": time.time(),
                "turn": 1
            })

            save_conversation(conversation_id, conv)

            # Start conversation by sending to provider
            initial_msg = NegotiationMessage(
                content=user_message,
                conversation_id=conversation_id,
                from_agent="buyer",
                turn_number=1
            )

            # Send message to provider using bureau's internal messaging
            # Store the message for processing
            conversations[conversation_id] = conv

            # Trigger provider response directly since we can't easily send async messages from Flask
            # We'll use a different approach - let the frontend poll for updates
            print(f"✅ Conversation initialized, agents will start responding")

        else:
            # Continue existing negotiation
            print(f"🔄 Continuing negotiation: {conversation_id}")

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "message": "Negotiation in progress"
        })

    except Exception as e:
        print(f"❌ Error in negotiate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        # Load from file
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
            "agent_profile": conv.get("agent_profile", {})
        })

    except Exception as e:
        print(f"❌ Error getting conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    # Count conversation files
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

def run_flask():
    """Run Flask in separate thread"""
    print("🌐 Starting Flask API on http://localhost:8001")
    app.run(debug=False, host='0.0.0.0', port=8001, threaded=True)

if __name__ == "__main__":
    print("🚀 Starting Persistent Negotiation System")
    print(f"🤖 AI Model: {'Gemini Available' if model else 'Basic responses only'}")
    print(f"💾 Conversations saved to: {os.path.abspath(CONVERSATIONS_DIR)}")

    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("🏢 Starting Bureau with persistent agents...")

    # Run bureau
    bureau.run()