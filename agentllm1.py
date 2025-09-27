# agent_ayush.py
import os, json, httpx
from dotenv import load_dotenv
from uagents import Agent, Context, Model
import pathlib
import json
from typing import Optional

PROFILE_PATH = "profile_plumber_marcus.json"
try:
    PROFILE_JSON_OBJ = json.loads(pathlib.Path(PROFILE_PATH).read_text(encoding="utf-8"))
    # Compact string version to include in chat
    PROFILE_TEXT = json.dumps(PROFILE_JSON_OBJ, ensure_ascii=False)
except FileNotFoundError:
    PROFILE_TEXT = "{}"  # fallback if file missing


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
SEED_PHRASE = "My_seed_underscore_phase7970"

agent = Agent(
    name="agent_Ayush",
    seed=SEED_PHRASE,
    port=8000,
    mailbox=True,                 # ✅ easiest cross-laptop communication
    readme_path="README.md",
    publish_agent_details=True,
    # endpoint=["http://localhost:8000/submit"],  # only if you want direct HTTP
)


PROMPT_PATH = "negotiator_universal.md"   # <-- your prompt file
PROMPT_TEXT = pathlib.Path(PROMPT_PATH).read_text(encoding="utf-8")

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

            {"role": "system", "content": f"{PROMPT_TEXT} Counterparty Profile (JSON):\n{PROFILE_TEXT}"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    ctx.logger.info(f"[ASI DEBUG] Sending to {url} with model={ASI_MODEL}")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        ctx.logger.info(f"[ASI DEBUG] HTTP {r.status_code}")
        ctx.logger.info(f"[ASI DEBUG] Raw body (first 500 chars): {r.text[:500]}")

    r.raise_for_status()
    data = r.json()

    if "choices" not in data:
        raise RuntimeError(f"ASI response missing choices: {data}")

    return data["choices"][0]["message"]["content"].strip()


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
