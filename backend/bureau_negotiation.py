"""
Compact negotiation pipeline using Fetch.ai uAgents + Bureau
This creates a robust, orchestrated system for agent-to-agent negotiation
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
from uagents import Agent, Context, Model, Bureau
from uagents.setup import fund_agent_if_low
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

# Message Models
class NegotiationMessage(Model):
    content: str
    conversation_id: str
    sender_type: str  # 'user' or 'agent'

class StartNegotiation(Model):
    user_message: str
    agent_profile: Dict[str, Any]
    conversation_id: str

class NegotiationResponse(Model):
    content: str
    conversation_id: str
    is_complete: bool

# Global conversation storage
conversations: Dict[str, Dict[str, Any]] = {}

# Create Bureau (use different port than Flask)
bureau = Bureau(port=8003, endpoint="http://localhost:8003/submit")

# Create Negotiation Coordinator Agent
coordinator = Agent(
    name="coordinator",
    seed="coordinator_seed_123",
    port=8003,
)

# Create Service Provider Agent
service_agent = Agent(
    name="service_provider",
    seed="service_provider_seed_456",
    port=8004,
)

def create_negotiation_prompt(agent_profile: Dict, conversation_history: List[Dict]) -> str:
    """Create a negotiation prompt based on agent profile and conversation history"""

    history_text = ""
    for msg in conversation_history:
        role = "Customer" if msg["role"] == "user" else "You"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are {agent_profile.get('name', 'a service provider')} - {agent_profile.get('job', 'a professional')}.
Your average price is ${agent_profile.get('averagePrice', 50)}/hr.
Description: {agent_profile.get('description', 'I provide quality services')}

You are in a negotiation with a customer. Be professional, helpful, and try to find a fair price that works for both parties.

Conversation so far:
{history_text}

Respond naturally as the service provider. Keep responses conversational and under 100 words.
If the customer seems ready to agree on terms, suggest finalizing the deal.
"""
    return prompt

def check_negotiation_complete(message: str) -> bool:
    """Check if negotiation is complete"""
    completion_keywords = [
        'deal', 'agreed', 'accept', 'perfect', 'sounds good', 'let\'s do it',
        'book', 'schedule', 'when can', 'finalize', 'confirm'
    ]
    return any(keyword in message.lower() for keyword in completion_keywords)

# Create conversations directory for local storage
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

def save_conversation_locally(conversation_id: str, conversation_data: Dict):
    """Save conversation to local JSON file"""
    try:
        filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
        with open(filepath, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        print(f"BUREAU: Saved conversation {conversation_id} locally")
    except Exception as e:
        print(f"BUREAU ERROR: Failed to save conversation {conversation_id}: {e}")

def load_conversation_locally(conversation_id: str) -> Dict:
    """Load conversation from local JSON file"""
    try:
        filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            print(f"BUREAU: Loaded conversation {conversation_id} from local file")
            return data
        return {}
    except Exception as e:
        print(f"BUREAU ERROR: Failed to load conversation {conversation_id}: {e}")
        return {}

def check_should_continue_with_gemini(conversation_history: List[Dict]) -> bool:
    """Use Gemini to intelligently determine if negotiation should continue"""
    if not model or len(conversation_history) < 2:
        return False

    # Get recent messages for analysis
    recent_messages = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history

    history_text = ""
    for msg in recent_messages:
        role = "Customer" if msg["role"] == "user" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    analysis_prompt = f"""
Analyze this negotiation conversation and determine if it should CONTINUE or is COMPLETE.

Conversation:
{history_text}

A negotiation should CONTINUE when:
- Still discussing price, terms, or service details
- Either party is asking questions or requesting clarification
- Negotiating scope, timeline, or specific requirements
- No clear agreement has been reached yet
- Either party is considering the offer

A negotiation is COMPLETE when:
- Both parties have clearly agreed on price and terms
- Someone explicitly accepts the deal (e.g., "sounds good", "let's do it", "deal")
- Clear next steps are agreed upon (booking, scheduling, contract)
- Final terms are confirmed and accepted

Respond with ONLY "CONTINUE" or "COMPLETE" - nothing else.
"""

    try:
        response = model.generate_content(analysis_prompt)
        result = response.text.strip().upper()

        print(f"BUREAU: Gemini continuation check: {result}")

        if "COMPLETE" in result:
            return False  # Don't continue
        else:
            return True   # Continue negotiation

    except Exception as e:
        print(f"BUREAU ERROR: Gemini continuation check failed: {e}")
        # Fallback: continue if no clear completion keywords
        recent_text = " ".join([msg["content"].lower() for msg in recent_messages])
        complete_keywords = ['deal', 'agreed', 'book', 'schedule', 'sounds good', 'perfect', 'let\'s do it']
        return not any(keyword in recent_text for keyword in complete_keywords)

def generate_buyer_response(conversation_history: List[Dict], agent_profile: Dict, user_request: str) -> str:
    """Generate buyer response to continue negotiation"""
    if not model:
        return "I'm interested in your services. Can you tell me more about what you can offer within my budget?"

    history_text = ""
    for msg in conversation_history:
        role = "You" if msg["role"] == "user" else "Service Provider"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""
You are a customer who originally requested: {user_request}

Conversation so far:
{history_text}

You are negotiating with a {agent_profile.get('job', 'service provider')} who charges ${agent_profile.get('averagePrice', 50)}/hr.

Continue the negotiation by:
- Responding to their latest message
- Negotiating price and terms professionally
- Asking clarifying questions about the service
- Working toward a fair agreement
- Being willing to accept reasonable offers

Respond in under 50 words. Be natural and conversational.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"BUREAU ERROR: Buyer response generation failed: {e}")
        return "That's helpful information. Can you provide more details about the pricing and what's included?"

# Coordinator handles communication with frontend
@coordinator.on_message(model=StartNegotiation)
async def handle_start_negotiation(ctx: Context, sender: str, msg: StartNegotiation):
    ctx.logger.info(f"🚀 Starting negotiation: {msg.conversation_id}")

    # Initialize conversation
    conversations[msg.conversation_id] = {
        "messages": [{"role": "user", "content": msg.user_message}],
        "agent_profile": msg.agent_profile,
        "is_complete": False
    }

    # Forward to service agent
    negotiation_msg = NegotiationMessage(
        content=msg.user_message,
        conversation_id=msg.conversation_id,
        sender_type="user"
    )

    await ctx.send(service_agent.address, negotiation_msg)

@coordinator.on_message(model=NegotiationMessage)
async def handle_negotiation_message(ctx: Context, sender: str, msg: NegotiationMessage):
    ctx.logger.info(f"📨 Received message for conversation {msg.conversation_id}")

    if msg.conversation_id not in conversations:
        ctx.logger.error(f"❌ Unknown conversation: {msg.conversation_id}")
        return

    conv = conversations[msg.conversation_id]

    if msg.sender_type == "user":
        # User message - add to conversation and forward to service agent
        conv["messages"].append({"role": "user", "content": msg.content})
        await ctx.send(service_agent.address, msg)

    elif msg.sender_type == "agent":
        # Agent response - add to conversation
        conv["messages"].append({"role": "agent", "content": msg.content})

        # Check if negotiation is complete
        is_complete = check_negotiation_complete(msg.content)
        conv["is_complete"] = is_complete

        if is_complete:
            ctx.logger.info(f"🏁 Negotiation {msg.conversation_id} completed!")

# Service Provider handles the actual negotiation logic
@service_agent.on_message(model=NegotiationMessage)
async def handle_service_message(ctx: Context, sender: str, msg: NegotiationMessage):
    ctx.logger.info(f"🤖 Service agent processing: {msg.content}")

    if msg.conversation_id not in conversations:
        ctx.logger.error(f"❌ Unknown conversation: {msg.conversation_id}")
        return

    conv = conversations[msg.conversation_id]
    agent_profile = conv["agent_profile"]

    # Generate AI response
    if model:
        try:
            prompt = create_negotiation_prompt(agent_profile, conv["messages"])
            response = model.generate_content(prompt)
            agent_response = response.text.strip()
            ctx.logger.info(f"🤖 Generated response: {agent_response}")
        except Exception as e:
            ctx.logger.error(f"❌ Gemini error: {e}")
            agent_response = f"I understand you're looking for {agent_profile.get('job', 'services')}. Let me help you with that. What's your budget in mind?"
    else:
        agent_response = f"Thanks for reaching out! As a {agent_profile.get('job', 'professional')}, I typically charge ${agent_profile.get('averagePrice', 50)}/hr. What kind of timeline are you looking at?"

    # Send response back to coordinator
    response_msg = NegotiationMessage(
        content=agent_response,
        conversation_id=msg.conversation_id,
        sender_type="agent"
    )

    await ctx.send(coordinator.address, response_msg)

# Add agents to bureau
bureau.add(coordinator)
bureau.add(service_agent)

# Flask API for frontend communication
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# WebSocket event handlers
@socketio.on('join_conversation')
def on_join_conversation(data):
    conversation_id = data['conversation_id']
    print(f"🔌 WEBSOCKET: Client requesting to join conversation room: {conversation_id}")
    join_room(conversation_id)
    print(f"🔌 WEBSOCKET: Client successfully joined conversation room: {conversation_id}")
    emit('joined_conversation', {'conversation_id': conversation_id})
    print(f"🔌 WEBSOCKET: Sent confirmation to client for room: {conversation_id}")

@socketio.on('leave_conversation')
def on_leave_conversation(data):
    conversation_id = data['conversation_id']
    leave_room(conversation_id)
    print(f"Client left conversation room: {conversation_id}")

@socketio.on('connect')
def on_connect():
    print('🔌 WEBSOCKET: Client connected to WebSocket')
    print(f'🔌 WEBSOCKET: Total connected clients: {len(socketio.server.manager.rooms)}')

@socketio.on('disconnect')
def on_disconnect():
    print('🔌 WEBSOCKET: Client disconnected from WebSocket')

@app.route('/negotiate', methods=['POST'])
def negotiate():
    """Start negotiation and continue until completion automatically"""
    print("🚀 NEGOTIATE: /negotiate endpoint called")
    try:
        print("🚀 NEGOTIATE: Starting negotiation process")

        # Get and validate request data
        if not request.is_json:
            print("BUREAU ERROR: Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        if not data:
            print("BUREAU ERROR: No JSON data received")
            return jsonify({"error": "No JSON data provided"}), 400

        print(f"BUREAU: Received data: {data}")

        conversation_id = data.get('conversation_id', f'conv_{int(time.time())}')
        user_message = data.get('message', '')
        agent_profile = data.get('agent_profile', {})

        print(f"BUREAU: Parsed - ID: {conversation_id}")
        print(f"BUREAU: Message: '{user_message}'")
        print(f"BUREAU: Profile: {agent_profile}")

        if not user_message:
            print("BUREAU ERROR: No user message provided")
            return jsonify({"error": "No message provided"}), 400

        print(f"BUREAU: Starting continuous negotiation for {conversation_id}")

        # Load existing conversation or create new one
        conv = load_conversation_locally(conversation_id)
        if not conv:
            print(f"BUREAU: Creating new conversation {conversation_id}")
            conv = {
                "conversation_id": conversation_id,
                "messages": [{"role": "user", "content": user_message}],
                "agent_profile": agent_profile,
                "user_request": user_message,
                "is_complete": False,
                "created_at": time.time()
            }
        else:
            print(f"BUREAU: Updating existing conversation {conversation_id}")
            conv["messages"].append({
                "role": "user",
                "content": user_message
            })

        # Store initial conversation
        conversations[conversation_id] = conv
        save_conversation_locally(conversation_id, conv)
        
        # Emit initial user message via WebSocket
        print(f"🔌 WEBSOCKET: Emitting initial user message to room {conversation_id}")
        print(f"🔌 WEBSOCKET: Message content: {user_message}")
        print(f"🔌 WEBSOCKET: Checking if room {conversation_id} has clients...")
        # Check room occupancy
        if conversation_id in socketio.server.manager.rooms:
            room_clients = len(socketio.server.manager.rooms[conversation_id])
            print(f"🔌 WEBSOCKET: Room {conversation_id} has {room_clients} clients")
        else:
            print(f"🔌 WEBSOCKET: Room {conversation_id} does not exist yet")
        socketio.emit('new_message', {
            'role': 'user',
            'content': user_message,
            'conversation_id': conversation_id
        }, room=conversation_id)
        print(f"🔌 WEBSOCKET: Initial user message emitted successfully")

        max_turns = 20  # Prevent infinite loops
        turn_count = 0

        print(f"🚀 NEGOTIATE: Starting negotiation loop with max {max_turns} turns")
        while turn_count < max_turns:
            turn_count += 1
            print(f"🚀 NEGOTIATE: Turn {turn_count}/{max_turns}")

            # Generate agent response
            agent_response = ""
            if model:
                try:
                    print("BUREAU: Generating AI response with Gemini...")
                    prompt = create_negotiation_prompt(agent_profile, conv["messages"])
                    response = model.generate_content(prompt)
                    agent_response = response.text.strip()
                    print(f"BUREAU: Agent response: {agent_response}")
                except Exception as e:
                    print(f"BUREAU ERROR: Gemini error: {e}")
                    agent_response = f"I understand you're looking for {agent_profile.get('job', 'services')}. Let me help you with that. What's your budget in mind?"
            else:
                print("BUREAU: Using fallback response (no AI model)")
                agent_response = f"Thanks for reaching out! As a {agent_profile.get('job', 'professional')}, I typically charge ${agent_profile.get('averagePrice', 50)}/hr. What kind of timeline are you looking at?"

            # Add agent response
            conv["messages"].append({"role": "agent", "content": agent_response})
            save_conversation_locally(conversation_id, conv)
            
            # Emit agent response via WebSocket
            print(f"🔌 WEBSOCKET: Emitting agent response to room {conversation_id}")
            print(f"🔌 WEBSOCKET: Agent response: {agent_response}")
            print(f"🔌 WEBSOCKET: Checking if room {conversation_id} has clients...")
            # Check room occupancy
            if conversation_id in socketio.server.manager.rooms:
                room_clients = len(socketio.server.manager.rooms[conversation_id])
                print(f"🔌 WEBSOCKET: Room {conversation_id} has {room_clients} clients")
            else:
                print(f"🔌 WEBSOCKET: Room {conversation_id} does not exist yet")
            socketio.emit('new_message', {
                'role': 'agent',
                'content': agent_response,
                'conversation_id': conversation_id
            }, room=conversation_id)
            print(f"🔌 WEBSOCKET: Agent response emitted successfully")

            # Check if negotiation should continue using Gemini
            should_continue = check_should_continue_with_gemini(conv["messages"])
            print(f"BUREAU: Should continue? {should_continue}")

            if not should_continue:
                print(f"BUREAU: Negotiation {conversation_id} completed after {turn_count} turns!")
                conv["is_complete"] = True
                conv["completed_at"] = time.time()
                conv["completion_reason"] = "agreement_reached"
                save_conversation_locally(conversation_id, conv)
                conversations[conversation_id] = conv
                
                # Emit negotiation completion via WebSocket
                print(f"🔌 WEBSOCKET: Emitting negotiation completion to room {conversation_id}")
                socketio.emit('negotiation_complete', {
                    'conversation_id': conversation_id,
                    'completion_reason': 'agreement_reached',
                    'turns': turn_count
                }, room=conversation_id)
                print(f"🔌 WEBSOCKET: Negotiation completion emitted successfully")

                return jsonify({
                    "success": True,
                    "conversation_id": conversation_id,
                    "is_complete": True,
                    "messages": conv["messages"],
                    "turn_count": turn_count,
                    "completion_reason": "agreement_reached"
                })

            # Generate buyer response to continue negotiation
            buyer_response = generate_buyer_response(
                conv["messages"],
                agent_profile,
                conv["user_request"]
            )
            print(f"BUREAU: Buyer response: {buyer_response}")

            # Add buyer response
            conv["messages"].append({"role": "user", "content": buyer_response})
            save_conversation_locally(conversation_id, conv)
            
            # Emit buyer response via WebSocket
            print(f"🔌 WEBSOCKET: Emitting buyer response to room {conversation_id}")
            print(f"🔌 WEBSOCKET: Buyer response: {buyer_response}")
            socketio.emit('new_message', {
                'role': 'user',
                'content': buyer_response,
                'conversation_id': conversation_id
            }, room=conversation_id)
            print(f"🔌 WEBSOCKET: Buyer response emitted successfully")

            # Check again after buyer response
            should_continue = check_should_continue_with_gemini(conv["messages"])
            print(f"BUREAU: Should continue after buyer response? {should_continue}")

            if not should_continue:
                print(f"BUREAU: Negotiation {conversation_id} completed after buyer response at turn {turn_count}!")
                conv["is_complete"] = True
                conv["completed_at"] = time.time()
                conv["completion_reason"] = "agreement_reached"
                save_conversation_locally(conversation_id, conv)
                conversations[conversation_id] = conv

                return jsonify({
                    "success": True,
                    "conversation_id": conversation_id,
                    "is_complete": True,
                    "messages": conv["messages"],
                    "turn_count": turn_count,
                    "completion_reason": "agreement_reached"
                })

            # Small delay to prevent overwhelming the API
            time.sleep(0.5)

        # If we reach max turns, mark as complete
        print(f"BUREAU: Reached max turns ({max_turns}) for {conversation_id}")
        conv["is_complete"] = True
        conv["completed_at"] = time.time()
        conv["completion_reason"] = "max_turns_reached"
        save_conversation_locally(conversation_id, conv)
        conversations[conversation_id] = conv

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "is_complete": True,
            "messages": conv["messages"],
            "turn_count": turn_count,
            "completion_reason": "max_turns_reached"
        })

    except Exception as e:
        print(f"BUREAU CRITICAL ERROR: in negotiate endpoint")
        print(f"BUREAU ERROR: Error type: {type(e).__name__}")
        print(f"BUREAU ERROR: Error message: {str(e)}")

        import traceback
        error_traceback = traceback.format_exc()
        print(f"BUREAU: Full traceback: {error_traceback}")

        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_traceback
        }), 500

@app.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        conv = conversations.get(conversation_id, {"messages": [], "is_complete": False})

        return jsonify({
            "messages": conv["messages"],
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
        "ai_available": model is not None,
        "bureau_running": True
    })

def run_flask():
    """Run Flask with SocketIO in a separate thread"""
    print("FLASK: Starting Flask API with WebSocket support on http://localhost:8001")
    socketio.run(app, debug=False, host='0.0.0.0', port=8001, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    print("BUREAU: Starting Bureau-based Negotiation System")
    print(f"AI Model: {'Gemini Available' if model else 'Fallback responses only'}")

    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("BUREAU: Starting Bureau with agents...")

    # Run the bureau
    bureau.run()