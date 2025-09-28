"""
Simple, robust negotiation service for frontend
No complex agent orchestration - just works!
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from typing import Dict, List, Any
from dotenv import load_dotenv
import google.generativeai as genai

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
    print("⚠️ No Gemini API key - using fallback responses")

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# In-memory conversation storage
conversations: Dict[str, Dict[str, Any]] = {}

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
        'book', 'schedule', 'when can', 'finalize', 'confirm', 'yes', 'okay'
    ]
    return any(keyword in message.lower() for keyword in completion_keywords)

@app.route('/negotiate', methods=['POST'])
def negotiate():
    """Main negotiation endpoint"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        conversation_id = data.get('conversation_id', 'default')
        user_message = data.get('message', '')
        agent_profile = data.get('agent_profile', {})

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        print(f"🔥 NEGOTIATION: Conversation {conversation_id}")
        print(f"📨 User: {user_message}")
        print(f"🤖 Agent: {agent_profile.get('name', 'Unknown')}")

        # Initialize or update conversation
        if conversation_id not in conversations:
            conversations[conversation_id] = {
                "messages": [],
                "agent_profile": agent_profile,
                "is_complete": False
            }

        conv = conversations[conversation_id]

        # Add user message
        conv["messages"].append({"role": "user", "content": user_message})

        # Generate AI response
        if model:
            try:
                prompt = create_negotiation_prompt(agent_profile, conv["messages"])
                response = model.generate_content(prompt)
                agent_response = response.text.strip()
                print(f"🤖 Agent response: {agent_response}")
            except Exception as e:
                print(f"❌ Gemini error: {e}")
                agent_response = f"I understand you're looking for {agent_profile.get('job', 'services')}. Let me help you with that. What's your budget in mind?"
        else:
            # Fallback response
            avg_price = agent_profile.get('averagePrice', 50)
            job = agent_profile.get('job', 'professional services')
            agent_response = f"Thanks for reaching out! As a {job} provider, I typically charge ${avg_price}/hr. What kind of timeline are you looking at?"

        # Add agent response
        conv["messages"].append({"role": "agent", "content": agent_response})

        # Check if negotiation is complete
        is_complete = check_negotiation_complete(agent_response) or check_negotiation_complete(user_message)
        conv["is_complete"] = is_complete

        if is_complete:
            print(f"🏁 Negotiation {conversation_id} completed!")

        return jsonify({
            "success": True,
            "agent_response": agent_response,
            "is_complete": is_complete,
            "conversation_id": conversation_id
        })

    except Exception as e:
        print(f"❌ Error in negotiate: {e}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/conversations', methods=['GET'])
def list_conversations():
    """List all conversations"""
    try:
        conv_list = []
        for conv_id, conv_data in conversations.items():
            conv_list.append({
                "id": conv_id,
                "message_count": len(conv_data.get("messages", [])),
                "is_complete": conv_data.get("is_complete", False),
                "agent_name": conv_data.get("agent_profile", {}).get("name", "Unknown")
            })

        return jsonify({"conversations": conv_list})

    except Exception as e:
        print(f"❌ Error listing conversations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "conversations": len(conversations),
        "ai_available": model is not None
    })

if __name__ == '__main__':
    print("🚀 Starting Simple Negotiation Server")
    print("🌐 API available at http://localhost:8001")
    print(f"🤖 AI Model: {'Gemini Available' if model else 'Fallback responses only'}")
    app.run(debug=True, host='0.0.0.0', port=8001)