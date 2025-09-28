# Demo LangGraph Negotiation with Mock Responses (no API dependency)
import os, json, asyncio
from typing import TypedDict, Literal
from uagents import Agent, Context, Model
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

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

# Mock negotiation responses
MOCK_RESPONSES = [
    "I'm interested! But $150 seems a bit high. Would you consider $120?",
    "That's still more than I was hoping to spend. How about $110?",
    "I could go up to $125, that's really my final offer.",
    "Alright, I can meet you at $130. Deal? NEGOTIATION_COMPLETE."
]

# Agent setup
agent = Agent(
    name="demo_negotiator",
    seed="demo_seed",
    port=8040,
    endpoint=["http://127.0.0.1:8040/submit"],
    mailbox=False
)

# Global state
current_negotiation_state = {}
memory = MemorySaver()

# Mock response generator
def get_mock_response(round_num: int) -> str:
    if round_num - 1 < len(MOCK_RESPONSES):
        return MOCK_RESPONSES[round_num - 1]
    return "I think we should wrap this up. NEGOTIATION_COMPLETE."

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
    elif state["negotiation_round"] > 8:  # Max rounds
        state["status"] = "failed"
    else:
        state["status"] = "active"

    return state

def generate_negotiation_response(state: NegotiationState) -> NegotiationState:
    """Generate mock negotiation response"""

    # Use mock responses instead of API
    response = get_mock_response(state["negotiation_round"])
    state["current_offer"] = response

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
    workflow.add_node("generate_response", generate_negotiation_response)

    # Add edges
    workflow.add_edge("process_message", "generate_response")

    # Add conditional edge - THIS IS THE KEY PART!
    workflow.add_conditional_edges(
        "generate_response",
        check_negotiation_complete,
        {
            "continue": "process_message",  # Loop back to continue negotiation
            "end": END                      # 🎯 THIS ROUTES TO END!
        }
    )

    # Set entry point
    workflow.set_entry_point("process_message")

    return workflow.compile(checkpointer=memory)

# Create the graph
negotiation_graph = create_negotiation_graph()

@agent.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info(f"🎭 Demo LangGraph Negotiator live. Address: {agent.address}")

    # Wait for other agents to be ready
    await asyncio.sleep(2)

    # Send initial message
    test_partner = 'agent1qtxhgf0s9t3hqwsyxen6ujkyqnrqaf2rgf2f0klapr7svede3kgd6eqru8x'
    ctx.logger.info(f"🚀 Starting demo negotiation with {test_partner}")
    await ctx.send(test_partner, Message(message="Hello! I have an iPad for sale at $150. Are you interested in negotiating?"))

@agent.on_message(model=Message)
async def on_negotiation_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"📨 Received: {msg.message} (from {sender})")

    # Check if negotiation is already complete
    if "NEGOTIATION_COMPLETE" in msg.message.upper():
        ctx.logger.info("🏁 Negotiation completed! LangGraph reached END state.")
        return

    # Get or create negotiation state
    thread_id = f"negotiation_{sender}"

    current_state = current_negotiation_state.get(sender, {
        "messages": [],
        "current_offer": "",
        "negotiation_round": 0,
        "status": "active",
        "final_agreement": ""
    })

    # Add new message to state
    current_state["messages"].append(msg.message)

    # Process through LangGraph
    config = {"configurable": {"thread_id": thread_id}}
    result = await negotiation_graph.ainvoke(current_state, config=config)

    # Update stored state
    current_negotiation_state[sender] = result

    # Send response
    response_msg = result["current_offer"]
    await ctx.send(sender, Message(message=response_msg))

    # Log negotiation status
    if result["status"] == "completed":
        ctx.logger.info(f"✅ LangGraph COMPLETED! Conditional edge routed to END!")
        ctx.logger.info(f"🏆 Final agreement: {result['final_agreement']}")
    elif result["status"] == "failed":
        ctx.logger.info(f"❌ LangGraph FAILED! Conditional edge routed to END after {result['negotiation_round']} rounds")
    else:
        ctx.logger.info(f"🔄 LangGraph CONTINUING - Round {result['negotiation_round']}")

if __name__ == "__main__":
    print("🎭 Starting Demo LangGraph Negotiation...")
    print("🎯 This demo shows LangGraph conditional edges routing to END")
    print("📋 Features:")
    print("  - Mock responses (no API needed)")
    print("  - Real LangGraph state management")
    print("  - Conditional edge logic")
    print("  - Routes to END when complete")
    agent.run()