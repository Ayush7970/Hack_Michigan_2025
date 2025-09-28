from pydantic import BaseModel
from uagents import Agent, Context, Model
from typing import List, Dict, Optional
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
x = os.getenv('GEMINI_API_KEY')
os.environ["GEMINI_API_KEY"] = x
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

form_agent = Agent(
    name="form-agent",
    port=8100,
    seed="form agent",
    endpoint=["http://localhost:8100/submit"],
)

class FormData(Model):
    name: str = ""
    job: str = ""
    averagePrice: float = 0.0
    tags: List[str] = []
    location: List[str] = []
    description: str = ""
    message: Optional[str] = None
    availability: List[str] = []

class InputMessage(Model):
    message: str

conversation_history: List[Dict[str, str]] = []

@form_agent.on_rest_post("/rest/post", request=InputMessage, response=FormData)
async def handle_form_submission(ctx: Context, req: InputMessage) -> FormData:
    try:
        conversation_history.append({"role": "user", "content": req.message})
        ctx.logger.info(f"Received data")
        
        message = req.message
        if not message:
            return {"error": "No message provided"}
        
        ctx.logger.info(f"Processing message: {message}")
        
        prompt = f"""
        You are a form processing agent. Extract the following fields from the user's message:
        - name: The name of the product or service
        - job: The type of job (e.g., developer, designer)
        - averagePrice: The average price for the service (as a number)
        - tags: A list of relevant tags (e.g., remote, full-time)
        - location: A list indicating if the job is remote or offline
        - description: A brief description of the product or service

        User's message: {message}

        History of conversation: {json.dumps(conversation_history)}

        IMPORANT:
        - Check the message history for relevant information, and to check whether the user has already provided some of the fields.
        - If the user's message does not contain enough information, give back questions to ask the user for the missing information. Do NOT make up any information.
        - Else if the information is complete:
        Respond with ONLY valid JSON in this exact format:
        {{
            "name": "string",
            "job": "string", 
            "averagePrice": 0.0,
            "tags": ["string1", "string2"],
            "location": ["remote" or "offline"],
            "description": "string",
            "availability": ["monday", "tuesday", "other days...]
        }}

        SCENARIOS:
        - If the user wants you to give advice or want you to generate something, respond with good advice and work with user's request. Do NOT return JSON in this case. You can generate and ask for confirmation.
        """
    
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        ctx.logger.info(f"Raw Gemini response: {content}")
        
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        else:
            conversation_history.append({"role": "assistant", "content": content})
            return FormData(
                name="",
                job="",
                averagePrice=0.0,
                tags=[],
                location=[],
                description="",
                message=content
            )
        
        data = json.loads(content)
        ctx.logger.info(f"Parsed data: {data}")
        
        return data
        
    except Exception as e:
        ctx.logger.error(f"Error: {e}")
        return {"error": str(e)}
    
if __name__ == "__main__":
    form_agent.run()