import requests, os, json
from uagents import Agent, Context, Model
from dotenv import load_dotenv
load_dotenv()  

ASI_API_KEY = os.getenv("ASI_ONE_API_KEY")

# ASI_BASE_URL = os.getenv("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_MODEL   = os.getenv("ASI_ONE_MODEL", "asi1-mini")

url = "https://api.asi1.ai/v1/chat/completions"
headers = {
"Authorization": f"Bearer {os.getenv('ASI_ONE_API_KEY')}",
"Content-Type": "application/json"
}
body = {
"model": "asi1-mini",
"messages": [{"role": "user", "content": "Hello! How can you help me today?"}]
}
# print(requests.post(url, headers=headers, json=body).json()["choices"][0]["message"]["content"])
agent = Agent(
    name="agent_Ayush",
    seed='something',
    port=8000,
    mailbox=False
)

class Message(Model):
    message: str

async def call_asi_one(ctx: Context, prompt: str) -> str:
    body = {
"model": "asi1-mini",
"messages": [{"role": "user", "content": prompt}]
}
    data = (requests.post(url, headers=headers, json=body).json()["choices"][0]["message"]["content"])

    # OpenAI-style parsing
    return data

# ---------- events ----------
@agent.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info(f"Agent live. Address: {agent.address}")

@agent.on_message(model=Message)
async def on_msg(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Got: {msg.message} (from {sender})")
    try:
        reply = await call_asi_one(ctx, msg.message)
    except Exception as e:
        reply = f"Sorry, ASI error: {e}"
        ctx.logger.error(reply)

    await ctx.send(sender, Message(message=reply))
    ctx.logger.info(f"Replied to {sender}")

# ---------- run ----------
if __name__ == "__main__":
    agent.run()