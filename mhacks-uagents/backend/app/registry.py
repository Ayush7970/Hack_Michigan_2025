from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import db, models, schemas

router = APIRouter()

def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@router.post("/agents")
def register_agent(agent: schemas.AgentProfile, db: Session = Depends(get_db)):
    # Check if agent already exists
    existing_agent = db.query(models.Agent).filter(models.Agent.agent_id == agent.agent_id).first()
    if existing_agent:
        # Update existing agent
        existing_agent.profile = agent.dict()
        db.commit()
        return {"status": "updated", "agent_id": agent.agent_id}
    else:
        # Create new agent
        db_agent = models.Agent(agent_id=agent.agent_id, profile=agent.dict())
        db.add(db_agent)
        db.commit()
        return {"status": "created", "agent_id": agent.agent_id}

@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter(models.Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent_id": agent.agent_id, "profile": agent.profile}

@router.get("/agents")
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(models.Agent).all()
    return [{"agent_id": agent.agent_id, "profile": agent.profile} for agent in agents]

@router.post("/requests")
def create_request(req: schemas.ServiceRequest, db: Session = Depends(get_db)):
    # Check if request already exists
    existing_req = db.query(models.Request).filter(models.Request.request_id == req.request_id).first()
    if existing_req:
        raise HTTPException(status_code=400, detail="Request ID already exists")
    
    db_req = models.Request(
        request_id=req.request_id,
        requester_id=req.requester_id,
        data=req.dict()
    )
    db.add(db_req)
    db.commit()
    return {"status": "created", "request_id": req.request_id}

@router.get("/requests/{request_id}")
def get_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(models.Request).filter(models.Request.request_id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"request_id": req.request_id, "data": req.data}

@router.get("/requests")
def list_requests(db: Session = Depends(get_db)):
    requests = db.query(models.Request).all()
    return [{"request_id": req.request_id, "data": req.data} for req in requests]
