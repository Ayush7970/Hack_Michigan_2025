# Test client to send messages to LangGraph negotiator
import asyncio
from uagents import Agent, Context, Model

class Message(Model):
    message: str

# Test client agent
client = Agent(
    name="test_client",
    seed="test_client_seed",
    port=8025,
    mailbox=False
)

@client.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info(f"Test client live. Address: {client.address}")

    # Wait a moment for the negotiator to be ready
    await asyncio.sleep(2)

    # Send initial negotiation message to LangGraph negotiator
    # You'll need to replace this with the actual address from langgraph_negotiator.py
    negotiator_address = "REPLACE_WITH_LANGGRAPH_NEGOTIATOR_ADDRESS"

    initial_message = "Hello! I want to buy an iPad for $105. Can we negotiate on this price?"

    ctx.logger.info(f"Sending negotiation message to {negotiator_address}")
    await ctx.send(negotiator_address, Message(message=initial_message))

@client.on_message(model=Message)
async def handle_response(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received response: {msg.message}")

    # You can add logic here to continue the negotiation
    # For example, respond based on the message content
    if "NEGOTIATION_COMPLETE" not in msg.message.upper():
        # Continue negotiating
        follow_up = "That's still too high for me. What's the lowest you can go?"
        await ctx.send(sender, Message(message=follow_up))

if __name__ == "__main__":
    print("🧪 Starting test client...")
    print("📝 Instructions:")
    print("1. First start langgraph_negotiator.py")
    print("2. Copy its agent address")
    print("3. Update negotiator_address in this file")
    print("4. Run this test client")
    client.run()