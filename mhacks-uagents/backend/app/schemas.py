from pydantic import BaseModel
from typing import List, Dict, Optional

class AgentProfile(BaseModel):
    agent_id: str
    owner: str
    services: List[str]
    pricing: Dict[str, Dict]
    location: Dict[str, float]
    availability: List[Dict]
    attributes: Dict
    policy: Dict

class ServiceRequest(BaseModel):
    request_id: str
    requester_id: str
    service: str
    location: Dict[str, float]
    constraints: Dict
    preferences: Dict
    metadata: Optional[Dict] = None

class ContractSchema(BaseModel):
    session_id: str
    contract: Dict
