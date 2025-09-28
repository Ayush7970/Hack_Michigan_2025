"""
Two-Agent Negotiation System with Gemini Completion Detection
- Buyer Agent (represents the user)
- Service Provider Agent (the actual service provider)
- Gemini LLM monitors conversation and detects completion
"""

import asyncio
import os
from typing import Dict, List, Any
from uagents import Agent, Context, Model, Bureau
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import json
import time

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

# Message Models
class NegotiationMessage(Model):
    content: str
    conversation_id: str
    from_agent: str
    message_count: int

class StartNegotiation(Model):
    user_message: str
    agent_profile: Dict[str, Any]
    conversation_id: str

# Global storage
conversations: Dict[str, Dict[str, Any]] = {}
active_negotiations: Dict[str, bool] = {}

# Create Bureau
bureau = Bureau(port=8003, endpoint="http://localhost:8003/submit")

# Buyer Agent (represents the user)
buyer_agent = Agent(
    name="buyer",
    seed="buyer_seed_12345",
    port=8003,
)

# Service Provider Agent
provider_agent = Agent(
    name="provider",
    seed="provider_seed_67890",
    port=8004,
)

def create_buyer_prompt(conversation_history: List[Dict], user_request: str) -> str:
    """Create prompt for buyer agent"""

    history_text = ""
    for msg in conversation_history:
        role = "You" if msg["from"] == "buyer" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are a customer looking for: {user_request}

Conversation so far:
{history_text}

You should:
- Negotiate price and terms professionally
- Ask clarifying questions about the service
- Try to get a fair deal
- Be reasonable but protect your interests
- If you're satisfied with the offer, accept it

Respond as the customer in under 50 words. Be conversational and natural.
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

You should:
- Provide helpful information about your services
- Negotiate price fairly
- Be professional and friendly
- Try to close the deal when appropriate
- Explain your value proposition

Respond as the service provider in under 50 words. Be conversational and natural.
"""
    return prompt

def check_negotiation_complete_with_gemini(conversation_history: List[Dict]) -> bool:
    """Use Gemini to intelligently detect if negotiation is complete"""

    if not model or len(conversation_history) < 2:
        return False

    # Get last few messages
    recent_messages = conversation_history[-4:] if len(conversation_history) >= 4 else conversation_history

    history_text = ""
    for msg in recent_messages:
        role = "Customer" if msg["from"] == "buyer" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    completion_prompt = f"""
Analyze this negotiation conversation and determine if the negotiation is COMPLETE.

A negotiation is COMPLETE when:
- Both parties have agreed on price and terms
- A deal has been accepted
- Someone says they'll book/schedule the service
- Clear agreement is reached (e.g., "sounds good", "deal", "let's do it")

Conversation:
{history_text}

Respond with ONLY "COMPLETE" or "CONTINUE" - nothing else.
"""

    try:
        response = model.generate_content(completion_prompt)
        result = response.text.strip().upper()

        print(f"🧠 Gemini completion check: {result}")

        return "COMPLETE" in result

    except Exception as e:
        print(f"❌ Gemini completion check error: {e}")
        # Fallback to keyword detection
        recent_text = " ".join([msg["content"].lower() for msg in recent_messages])
        keywords = ['deal', 'agreed', 'accept', 'book', 'schedule', 'sounds good', 'let\'s do it', 'perfect']
        return any(keyword in recent_text for keyword in keywords)

# Buyer Agent Logic
@buyer_agent.on_message(model=StartNegotiation)
async def start_buyer_negotiation(ctx: Context, sender: str, msg: StartNegotiation):
    ctx.logger.info(f"🛒 Buyer starting negotiation: {msg.conversation_id}")

    # Initialize conversation
    conversations[msg.conversation_id] = {
        "messages": [],
        "agent_profile": msg.agent_profile,
        "user_request": msg.user_message,
        "is_complete": False
    }

    active_negotiations[msg.conversation_id] = True

    # Send initial message to provider
    initial_msg = NegotiationMessage(
        content=msg.user_message,
        conversation_id=msg.conversation_id,
        from_agent="buyer",
        message_count=1
    )

    # Add to conversation history
    conversations[msg.conversation_id]["messages"].append({
        "from": "buyer",
        "content": msg.user_message,
        "timestamp": time.time()
    })

    await ctx.send(provider_agent.address, initial_msg)

@buyer_agent.on_message(model=NegotiationMessage)
async def buyer_respond(ctx: Context, sender: str, msg: NegotiationMessage):

    if not active_negotiations.get(msg.conversation_id, False):
        ctx.logger.info(f"🛑 Buyer: Negotiation {msg.conversation_id} is no longer active")
        return

    ctx.logger.info(f"🛒 Buyer received: {msg.content}")

    conv = conversations.get(msg.conversation_id)
    if not conv:
        ctx.logger.error(f"❌ Unknown conversation: {msg.conversation_id}")
        return

    # Add provider message to history
    conv["messages"].append({
        "from": "provider",
        "content": msg.content,
        "timestamp": time.time()
    })

    # Check if negotiation is complete
    if check_negotiation_complete_with_gemini(conv["messages"]):
        ctx.logger.info(f"🏁 Buyer: Negotiation {msg.conversation_id} is COMPLETE!")
        active_negotiations[msg.conversation_id] = False
        conv["is_complete"] = True
        return

    # Generate buyer response using Gemini
    if model:
        try:
            prompt = create_buyer_prompt(conv["messages"], conv["user_request"])
            response = model.generate_content(prompt)
            buyer_response = response.text.strip()
            ctx.logger.info(f"🛒 Buyer response: {buyer_response}")
        except Exception as e:
            ctx.logger.error(f"❌ Buyer Gemini error: {e}")
            buyer_response = "That sounds interesting. Can you tell me more about the pricing and timeline?"
    else:
        buyer_response = "That sounds good. What would be your best price for this service?"

    # Add buyer response to history
    conv["messages"].append({
        "from": "buyer",
        "content": buyer_response,
        "timestamp": time.time()
    })

    # Check completion again after buyer response
    if check_negotiation_complete_with_gemini(conv["messages"]):
        ctx.logger.info(f"🏁 Buyer: Negotiation {msg.conversation_id} is COMPLETE after buyer response!")
        active_negotiations[msg.conversation_id] = False
        conv["is_complete"] = True
        return

    # Send response to provider
    response_msg = NegotiationMessage(
        content=buyer_response,
        conversation_id=msg.conversation_id,
        from_agent="buyer",
        message_count=msg.message_count + 1
    )

    await ctx.send(provider_agent.address, response_msg)

# Provider Agent Logic
@provider_agent.on_message(model=NegotiationMessage)
async def provider_respond(ctx: Context, sender: str, msg: NegotiationMessage):

    if not active_negotiations.get(msg.conversation_id, False):
        ctx.logger.info(f"🛑 Provider: Negotiation {msg.conversation_id} is no longer active")
        return

    ctx.logger.info(f"🔧 Provider received: {msg.content}")

    conv = conversations.get(msg.conversation_id)
    if not conv:
        ctx.logger.error(f"❌ Unknown conversation: {msg.conversation_id}")
        return

    # Add buyer message to history (if not already added)
    if not conv["messages"] or conv["messages"][-1]["content"] != msg.content:
        conv["messages"].append({
            "from": "buyer",
            "content": msg.content,
            "timestamp": time.time()
        })

    # Check if negotiation is complete
    if check_negotiation_complete_with_gemini(conv["messages"]):
        ctx.logger.info(f"🏁 Provider: Negotiation {msg.conversation_id} is COMPLETE!")
        active_negotiations[msg.conversation_id] = False
        conv["is_complete"] = True
        return

    # Generate provider response using Gemini
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
        "timestamp": time.time()
    })

    # Check completion again after provider response
    if check_negotiation_complete_with_gemini(conv["messages"]):
        ctx.logger.info(f"🏁 Provider: Negotiation {msg.conversation_id} is COMPLETE after provider response!")
        active_negotiations[msg.conversation_id] = False
        conv["is_complete"] = True
        return

    # Send response back to buyer
    response_msg = NegotiationMessage(
        content=provider_response,
        conversation_id=msg.conversation_id,
        from_agent="provider",
        message_count=msg.message_count + 1
    )

    await ctx.send(buyer_agent.address, response_msg)

# Add agents to bureau
bureau.add(buyer_agent)
bureau.add(provider_agent)

# Flask API for frontend
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

@app.route('/negotiate', methods=['POST'])
def start_negotiation():
    """Start a new negotiation between agents"""
    try:
        data = request.get_json()

        conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
        user_message = data.get('message', '')
        agent_profile = data.get('agent_profile', {})

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        print(f"🔥 Starting negotiation: {conversation_id}")
        print(f"📨 User request: {user_message}")
        print(f"🤖 Provider: {agent_profile.get('name', 'Unknown')}")

        # Send start message to buyer agent
        start_msg = StartNegotiation(
            user_message=user_message,
            agent_profile=agent_profile,
            conversation_id=conversation_id
        )

        # Add to bureau's message queue
        asyncio.run_coroutine_threadsafe(
            buyer_agent._send_message(buyer_agent.address, start_msg),
            asyncio.get_event_loop()
        )

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "message": "Negotiation started"
        })

    except Exception as e:
        print(f"❌ Error starting negotiation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        conv = conversations.get(conversation_id, {"messages": [], "is_complete": False})

        # Format messages for frontend
        formatted_messages = []
        for msg in conv["messages"]:
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
    return jsonify({
        "status": "healthy",
        "conversations": len(conversations),
        "active_negotiations": len([k for k, v in active_negotiations.items() if v]),
        "ai_available": model is not None
    })

def run_flask():
    """Run Flask in separate thread"""
    print("🌐 Starting Flask API on http://localhost:8001")
    app.run(debug=False, host='0.0.0.0', port=8001, threaded=True)

if __name__ == "__main__":
    print("🚀 Starting Two-Agent Negotiation System")
    print(f"🤖 AI Model: {'Gemini Available' if model else 'Basic responses only'}")

    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("🏢 Starting Bureau with negotiation agents...")
    print("🛒 Buyer Agent: Represents the user")
    print("🔧 Provider Agent: Represents the service provider")
    print("🧠 Gemini: Monitors conversation for completion")

    # Run bureau
    bureau.run()