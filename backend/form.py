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
    email: str = ""
    message: Optional[str] = None
    availability: List[str] = []
    completed: bool = False
    personality: str = ""

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
        - name: The name of the person providing the service
        - job: The type of job/service they provide (e.g., developer, designer, photographer)
        - averagePrice: The average price for the service (as a number)
        - tags: A list of relevant skills/tags
        - location: Location preferences ["remote", "offline", or specific cities]
        - description: A brief description of their services
        - email: Their email address for contact
        - availability: Days/times they are available
        - personality: Style of communication and how negotiative (e.g., friendly, professional). Ask to describe personality and work style.

        User's message: {message}

        History of conversation: {json.dumps(conversation_history)}

        IMPORTANT:
        - Check the message history for relevant information, and to check whether the user has already provided some of the fields.
        - REQUIRED FIELDS: name, job, averagePrice, email, description, personality. ALL of these must be provided before completion.
        - If ANY required field is missing, ask specific questions for the missing information. Do NOT make up any information.
        - If ALL required fields are complete, respond with JSON and set "completed": true
        - All fields MUST be filled, NOT EMPTY, with accurate information from the user. Do NOT fabricate any details.
        - DONT FORGET AVAILABILITY AND LOCATION

        When information is complete, respond with ONLY valid JSON in this exact format:
        {{
            "name": "string",
            "job": "string",
            "averagePrice": 0.0,
            "tags": ["string1", "string2"],
            "location": ["remote", "offline", or "city"],
            "description": "string",
            "email": "email@example.com",
            "availability": ["monday", "tuesday", "other days..."],
            "personality": "string",
            "completed": true
        }}

        SCENARIOS:
        - If the user wants advice or wants you to generate something, respond with good advice. Do NOT return JSON in this case.
        - If user provides partial info, ask for missing required fields: name, job, averagePrice, email, description, personality
        - Only set "completed": true when ALL required fields are provided
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
                email="",
                message=content,
                availability=[],
                completed=False,
                personality=""
            )
        
        data = json.loads(content)
        ctx.logger.info(f"Parsed data: {data}")

        # If the profile is completed, save to JSON file
        if data.get("completed", False):
            try:
                # Create filename from name (sanitized)
                name = data.get("name", "user").lower().replace(" ", "_").replace(".", "")
                filename = f"json_storage/{name}.json"

                # Prepare data structure to match existing format
                profile_data = {
                    "data": {
                        "name": data.get("name", ""),
                        "address": "",  # This might be set elsewhere
                        "job": data.get("job", ""),
                        "averagePrice": data.get("averagePrice", 0.0),
                        "tags": data.get("tags", []),
                        "location": data.get("location", []),
                        "email": data.get("email", ""),
                        "description": data.get("description", ""),
                        "availability": data.get("availability", []),
                        "personality": data.get("personality", "")
                    }
                }

                # Save to file
                with open(filename, 'w') as f:
                    json.dump(profile_data, f, indent=2)

                ctx.logger.info(f"Profile saved to {filename}")

                # Add completion message
                conversation_history.append({"role": "assistant", "content": "Profile completed successfully!"})

            except Exception as e:
                ctx.logger.error(f"Error saving profile: {e}")

        return data
        
    except Exception as e:
        ctx.logger.error(f"Error: {e}")
        return {"error": str(e)}
    
if __name__ == "__main__":
    form_agent.run()