# agent_ayush.py
import os, json, httpx
from dotenv import load_dotenv
from uagents import Agent, Context, Model
import pathlib
import json
from typing import Optional
import asyncio # can remve later 


START_CONVO = "yes"  # "yes" to initiate on startup



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
SEED_PHRASE = "clarissa_seed"

agent = Agent(
    name="bob",
    seed=SEED_PHRASE,
    port=8000,
    mailbox=True,                 # ✅ easiest cross-laptop communication
    readme_path="README.md",
    publish_agent_details=True,
    endpoint=["http://localhost:8000/submit"],  # Enable HTTP endpoints
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




async def prompt_cli(ctx: Context):
    """
    1) Ask for the opening message
    2) POST to your matchmaker to get a service uAgent address
    3) Send the message to that address
    """
    MATCHMAKER_URL = "https://literalistic-unadmitted-alton.ngrok-free.dev/match"

    # 1) collect the first message
    user_text = await asyncio.to_thread(input, "\nType your first message (enter to cancel): ")
    if not user_text.strip():
        ctx.logger.info("[USER] Cancelled, no message entered.")
        return

    # 2) call the matchmaker (expects JSON body with the user_text/description)
    payload = {"description": user_text}  # server hint: {"user_text": "..."}
    ctx.logger.info(f"[USER] Contacting matchmaker: {MATCHMAKER_URL}")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(MATCHMAKER_URL, json=payload)
        ctx.logger.info(f"[USER] Matchmaker HTTP {res.status_code}")
        res.raise_for_status()
    except Exception as e:
        ctx.logger.error(f"[USER] Matchmaker request failed: {e}")
        return
    # write your code here do not chagne other things 
    

    # 3) parse + store full response; extract the uAgent address separately
    try:
        data = res.json()
    except Exception as e:
        ctx.logger.error(f"[USER] Could not parse matchmaker JSON: {e}")
        return

    # Build a clean record and persist it (for debugging / reuse)
    match_record = {
        "message": data.get("message"),
        "matched_address": data.get("matched_address"),
        "match_score": data.get("match_score"),
        "matched_uagent": data.get("matched_uagent"),  # dict with name/job/desc/tags/averagePrice
        "status": data.get("status"),
        "request": {"description": user_text},
    }
    try:
        with open("last_match.json", "w", encoding="utf-8") as f:
            json.dump(match_record, f, ensure_ascii=False, indent=2)
        ctx.logger.info("[USER] Stored match details in last_match.json")
    except Exception as e:
        ctx.logger.error(f"[USER] Failed to write last_match.json: {e}")

    # Extract the uAgent address into a separate variable
    matched_uagent_address = data.get("matched_address")

    if not isinstance(matched_uagent_address, str) or not matched_uagent_address.strip():
        ctx.logger.error(f"[USER] No valid matched_address in response: {data}")
        return

    ctx.logger.info(f"[USER] Matched to service: {matched_uagent_address} (score={data.get('match_score')})")

    # 4) send the opening message to the matched service agent
    try:
        await ctx.send(matched_uagent_address, Message(message=user_text))
        ctx.logger.info("[USER] Sent opening message.")
    except Exception as e:
        ctx.logger.error(f"[USER] Failed to send message to {matched_uagent_address}: {e}")



class DirectMessage(Model):
    message: str

class SimpleResponse(Model):
    success: bool

# ---------- events ----------
@agent.on_rest_post("/submit", request=DirectMessage, response=SimpleResponse)
async def handle_direct_message(ctx: Context, req: DirectMessage) -> SimpleResponse:
    """Handle direct HTTP messages"""
    ctx.logger.info(f"🌐 BOB: Received direct HTTP message: {req.message}")

    try:
        # Process the message like a regular message
        reply = await call_asi_one(ctx, req.message)
        ctx.logger.info(f"🤖 BOB: Generated reply: {reply}")

        # For now, just log the reply (we'd need to send it back to scratch.py)
        # TODO: Send reply back to the calling agent

        return SimpleResponse(success=True)
    except Exception as e:
        ctx.logger.error(f"❌ BOB: Error processing direct message: {e}")
        return SimpleResponse(success=False)

@agent.on_event("startup")
async def on_start(ctx: Context):
    ctx.logger.info(f"Agent live. Address: {agent.address}")
    if START_CONVO == "yes":
        # short delay so mailbox is ready
        await asyncio.sleep(0.3)
        ctx.logger.info(f"Waiting for the prompt yes or no")

@agent.on_message(model=Message)
async def on_msg(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"🎯 BOB RECEIVED MESSAGE: {msg.message} (from {sender})")

    try:
        ctx.logger.info(f"🤖 Calling ASI API with message: {msg.message}")
        reply = await call_asi_one(ctx, msg.message)
        ctx.logger.info(f"🎯 ASI Response: {reply}")
    except Exception as e:
        reply = f"Sorry, ASI error: {e}"
        ctx.logger.error(f"❌ ASI Error: {reply}")

    ctx.logger.info(f"📤 Sending reply to {sender}: {reply}")
    await ctx.send(sender, Message(message=reply))
    ctx.logger.info(f"✅ Reply sent successfully to {sender}")

# ---------- run ----------
if __name__ == "__main__":
    agent.run()
