# LangGraph + uAgents Negotiation System
import os, json, httpx, pathlib
from typing import TypedDict, Literal
from dotenv import load_dotenv
from uagents import Agent, Context, Model
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
ASI_API_KEY = os.getenv("ASI_ONE_API_KEY")
ASI_MODEL = os.getenv("ASI_ONE_MODEL", "asi1-mini")

if not ASI_API_KEY:
    raise RuntimeError("ASI_ONE_API_KEY is missing. Put it in your .env")

try:
    PROMPT_TEXT = pathlib.Path("negotiator_universal.md").read_text(encoding="utf-8")
except FileNotFoundError:
    PROMPT_TEXT = """You are a skilled negotiator. Your goal is to reach a mutually beneficial agreement.
    Be professional, firm but fair, and work towards a resolution. When you believe the negotiation has concluded
    (either with an agreement or impasse), end your message with 'NEGOTIATION_COMPLETE'."""

# Message schema
class Message(Model):
    message: str

# LangGraph State
class NegotiationState(TypedDict):
    messages: list[str]
    current_offer: str
    negotiation_round: int
    status: Literal["active", "completed", "failed"]
    final_agreement: str

# Agent setup
SEED_PHRASE = "negotiator_agent"
agent = Agent(
    name="negotiator_agent",
    seed=SEED_PHRASE,
    port=8030,
    endpoint=["http://127.0.0.1:8030/submit"],  # Enable direct communication
    mailbox=False,  # Disabled to avoid subscription errors
    publish_agent_details=True,
)

# Global state for current negotiation
current_negotiation_state = {}
memory = MemorySaver()

# Error tracking to prevent infinite loops
api_error_count = {}
MAX_API_ERRORS = 3

# ASI API call
async def call_asi_one(ctx: Context, prompt: str, system_prompt: str = None) -> str:
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {ASI_API_KEY.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    messages = []
    if system_prompt and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    elif PROMPT_TEXT and PROMPT_TEXT.strip():
        messages.append({"role": "system", "content": PROMPT_TEXT})
    else:
        # Fallback if both are empty
        messages.append({"role": "system", "content": "You are a helpful negotiation assistant."})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": ASI_MODEL.strip(),
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
    }

    # Debug payload
    ctx.logger.info(f"[ASI DEBUG] Payload: {json.dumps(payload, indent=2)}")

    ctx.logger.info(f"[ASI DEBUG] Sending to {url} with model={ASI_MODEL}")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        ctx.logger.info(f"[ASI DEBUG] HTTP {r.status_code}")

    r.raise_for_status()
    data = r.json()

    if "choices" not in data:
        raise RuntimeError(f"ASI response missing choices: {data}")

    return data["choices"][0]["message"]["content"].strip()

# LangGraph Nodes
def process_negotiation_message(state: NegotiationState) -> NegotiationState:
    """Process incoming negotiation message and update state"""
    last_message = state["messages"][-1] if state["messages"] else ""

    # Increment round
    state["negotiation_round"] = state.get("negotiation_round", 0) + 1

    # Check if negotiation is complete
    if "NEGOTIATION_COMPLETE" in last_message.upper() or \
       any(phrase in last_message.upper() for phrase in [
           "DEAL", "AGREED", "ACCEPT", "FINAL OFFER", "CONCLUDED", "SETTLED"
       ]):
        state["status"] = "completed"
        state["final_agreement"] = last_message
    elif state["negotiation_round"] > 10:  # Max rounds
        state["status"] = "failed"
    else:
        state["status"] = "active"

    return state

async def generate_negotiation_response(state: NegotiationState, ctx: Context) -> NegotiationState:
    """Generate AI response for negotiation"""

    # Build context from message history
    context = f"""
    Negotiation Round: {state['negotiation_round']}
    Previous messages: {' | '.join(state['messages'][-3:]) if state['messages'] else 'None'}
    Current status: {state['status']}

    Generate your negotiation response. If you believe the negotiation should end,
    include 'NEGOTIATION_COMPLETE' in your response.
    """

    try:
        last_message = state["messages"][-1] if state["messages"] else "Let's begin negotiation"
        response = await call_asi_one(ctx, f"{context}\n\nRespond to: {last_message}")
        state["current_offer"] = response
        return state
    except Exception as e:
        ctx.logger.error(f"Error generating response: {e}")

        # Fallback responses based on negotiation state
        if state['negotiation_round'] > 5:
            state["current_offer"] = "Due to technical issues, I'm ending this negotiation. NEGOTIATION_COMPLETE."
            state["status"] = "failed"
        else:
            state["current_offer"] = "I apologize, but I'm having technical difficulties. Can we continue later?"
        return state

def check_negotiation_complete(state: NegotiationState) -> Literal["continue", "end"]:
    """Conditional edge to determine if negotiation should end"""
    if state["status"] in ["completed", "failed"]:
        return "end"
    return "continue"

# Build LangGraph
def create_negotiation_graph():
    workflow = StateGraph(NegotiationState)

    # Add nodes
    workflow.add_node("process_message", process_negotiation_message)
    workflow.add_node("generate_response", lambda state: generate_negotiation_response(state, None))  # We'll pass ctx later

    # Add edges
    workflow.add_edge("process_message", "generate_response")

    # Add conditional edge
    workflow.add_conditional_edges(
        "generate_response",
        check_negotiation_complete,
        {
            "continue": "process_message",
            "end": END
        }
    )

    # Set entry point
    workflow.set_entry_point("process_message")

    return workflow.compile(checkpointer=memory)

negotiation_graph = create_negotiation_graph()

@agent.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info(f"LangGraph Negotiator Agent live. Address: {agent.address}")

    # Wait a moment for other agents to be ready
    import asyncio
    await asyncio.sleep(3)

    # Send initial negotiation message to the other agent
    # This is the address for langgraph_negotiator_2.py with seed "wejkndwknedkwn"
    other_agent_address = 'agent1qtxhgf0s9t3hqwsyxen6ujkyqnrqaf2rgf2f0klapr7svede3kgd6eqru8x'
    ctx.logger.info(f"Sending initial negotiation message to {other_agent_address}")
    await ctx.send(other_agent_address, Message(message="Hello! I have an iPad for sale at $150. Are you interested in negotiating?"))

@agent.on_message(model=Message)
async def on_negotiation_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received negotiation message: {msg.message} (from {sender})")

    # Check if negotiation is already complete
    if "NEGOTIATION_COMPLETE" in msg.message.upper():
        ctx.logger.info("🏁 Negotiation already completed! No further responses needed.")
        return  # Don't respond to completed negotiations

    # Check for repeated technical difficulties
    if "technical difficulties" in msg.message.lower():
        api_error_count[sender] = api_error_count.get(sender, 0) + 1
        if api_error_count[sender] >= MAX_API_ERRORS:
            ctx.logger.info(f"🚫 Too many API errors from {sender}. Ending negotiation.")
            await ctx.send(sender, Message(message="Due to repeated technical issues, I'm ending this negotiation. NEGOTIATION_COMPLETE."))
            return

    # Get or create negotiation state for this sender
    thread_id = f"negotiation_{sender}"

    try:
        # Get current state or initialize
        current_state = current_negotiation_state.get(sender, {
            "messages": [],
            "current_offer": "",
            "negotiation_round": 0,
            "status": "active",
            "final_agreement": ""
        })

        # Add new message to state
        current_state["messages"].append(msg.message)

        # Update the generate_response function to use current context
        async def generate_response_with_ctx(state):
            return await generate_negotiation_response(state, ctx)

        # Temporarily update the node
        workflow = StateGraph(NegotiationState)
        workflow.add_node("process_message", process_negotiation_message)
        workflow.add_node("generate_response", generate_response_with_ctx)
        workflow.add_edge("process_message", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            check_negotiation_complete,
            {
                "continue": "process_message",
                "end": END
            }
        )
        workflow.set_entry_point("process_message")
        temp_graph = workflow.compile(checkpointer=memory)

        # Process through LangGraph
        config = {"configurable": {"thread_id": thread_id}}
        result = await temp_graph.ainvoke(current_state, config=config)

        # Update stored state
        current_negotiation_state[sender] = result

        # Send response
        response_msg = result["current_offer"]
        await ctx.send(sender, Message(message=response_msg))

        # Log negotiation status
        if result["status"] == "completed":
            ctx.logger.info(f"✅ Negotiation with {sender} completed successfully!")
            ctx.logger.info(f"Final agreement: {result['final_agreement']}")
        elif result["status"] == "failed":
            ctx.logger.info(f"❌ Negotiation with {sender} failed after {result['negotiation_round']} rounds")
        else:
            ctx.logger.info(f"🔄 Negotiation round {result['negotiation_round']} with {sender}")

    except Exception as e:
        ctx.logger.error(f"Error processing negotiation: {e}")
        await ctx.send(sender, Message(message="I apologize, but I encountered an error. Can we restart the negotiation?"))

if __name__ == "__main__":
    agent.run()