# agent_ayush.py
import os, json, httpx
from dotenv import load_dotenv
from uagents import Agent, Context, Model
import pathlib
import json
from typing import Optional, Dict, List, Literal

from dotenv import load_dotenv
load_dotenv()
x = os.getenv('GEMINI_API_KEY')
os.environ["GEMINI_API_KEY"] = x
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# ---------- load env ----------
load_dotenv()  # make sure .env is in this folder

ASI_API_KEY = os.getenv("ASI_ONE_API_KEY")

# ASI_BASE_URL = os.getenv("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_MODEL   = os.getenv("ASI_ONE_MODEL", "asi1-mini")

if not ASI_API_KEY:
    raise RuntimeError("ASI_ONE_API_KEY is missing. Put it in your .env")

# ---------- message schema ----------
class Message(Model):
    message: str

# ---------- agent ----------
SEED_PHRASE = "seed__111"

agent = Agent(
    name="agent_2",
    seed=SEED_PHRASE,
    port=8001,
    mailbox=True,                 # ✅ easiest cross-laptop communication
    readme_path="README.md",
    publish_agent_details=True,
    # endpoint=["http://localhost:8000/submit"],  # only if you want direct HTTP
)


PROMPT_PATH = "negotiator_universal.md"   # <-- your prompt file
PROMPT_TEXT = pathlib.Path(PROMPT_PATH).read_text(encoding="utf-8")

conversation_history: List[Dict[str, str]] = []

# ---------- asi:one client ----------
# ---------- asi:one client with debug logs ----------
async def call_asi_one(ctx: Context, prompt: str) -> str:
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {ASI_API_KEY.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": ASI_MODEL.strip(),
        "messages": [

            {"role": "system", "content": f"{PROMPT_TEXT}"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    ctx.logger.info(f"[ASI DEBUG] Sending to {url} with model={ASI_MODEL}")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        ctx.logger.info(f"[ASI DEBUG] HTTP {r.status_code}")

    r.raise_for_status()
    data = r.json()

    if "choices" not in data:
        raise RuntimeError(f"ASI response missing choices: {data}")

    return data["choices"][0]["message"]["content"].strip()

def check_negotiation_complete(message: str) -> bool:
    prompt = '''

    You are a negotiation assistant. Determine if the following message indicates that the negotiation is complete.
    Message: """{message}"""
    Important: Only respond with "true" or "false". Do NOT add any extra text.
    '''
    response = model.generate_content(prompt)

    mode = "a" if os.path.exists("debug_response.txt") and os.path.getsize("debug_response.txt") > 0 else "w"

    with open("debug_response.txt", mode) as f:
        f.write(f"Message: {conversation_history[-1]} and {conversation_history[-2]}\nResponse: {response.text}\n\n")
    if response.text.strip().lower() == "true":
        return True
    else:
        return False

# ---------- events ----------
@agent.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info(f"Agent live. Address: {agent.address}")
    await ctx.send('agent1q0xdga2g7twurf3f9cp3h2lhxs59vhmajq5ph44xqxpmc6d8ugs766yhnql', Message(message="Hello, can I get a plumbing service this Friday evening? My sink is leaking and I need it fixed urgently. My budget is around $100."))

@agent.on_message(model=Message)
async def on_msg(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Got: {msg.message} (from {sender})")
    conversation_history.append({"role": "user", "content": msg.message})

    try:
        reply = await call_asi_one(ctx, msg.message)
        conversation_history.append({"role": "assistant", "content": reply})
        ctx.logger.info(f"Our response: {reply}")
        ctx.logger.info(check_negotiation_complete(reply))
        if check_negotiation_complete(conversation_history):
            ctx.logger.info("🏁 Negotiation completed! Stopping responses.")
            return 
    except Exception as e:
        reply = f"Sorry, ASI error: {e}"
        ctx.logger.error(reply)

    await ctx.send(sender, Message(message=reply))
    ctx.logger.info(f"Replied to {sender}")

# ---------- run ----------
if __name__ == "__main__":
    agent.run()