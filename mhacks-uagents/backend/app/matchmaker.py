from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import db, models, utils
from typing import List, Dict, Any

router = APIRouter()

def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@router.get("/match/{request_id}")
def match_agents(request_id: str, limit: int = 5, db: Session = Depends(get_db)):
    """Find and rank agents that can fulfill a request."""
    req = db.query(models.Request).filter(models.Request.request_id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # Get all agents
    agents = db.query(models.Agent).all()
    agent_list = [{"agent_id": agent.agent_id, "profile": agent.profile} for agent in agents]
    
    # Rank agents based on the request
    ranked_agents = utils.rank_agents(agent_list, req.data)
    
    # Return top candidates
    candidates = ranked_agents[:limit]
    
    return {
        "request_id": request_id,
        "candidates": [{"agent_id": agent["agent_id"], "score": agent["score"]} for agent in candidates],
        "total_matches": len(ranked_agents)
    }

@router.post("/match/{request_id}/create_session")
def create_negotiation_session(request_id: str, agent_ids: List[str], db: Session = Depends(get_db)):
    """Create a negotiation session with specific agents for a request."""
    req = db.query(models.Request).filter(models.Request.request_id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Verify all agents exist
    agents = db.query(models.Agent).filter(models.Agent.agent_id.in_(agent_ids)).all()
    if len(agents) != len(agent_ids):
        found_ids = [agent.agent_id for agent in agents]
        missing_ids = [aid for aid in agent_ids if aid not in found_ids]
        raise HTTPException(status_code=404, detail=f"Agents not found: {missing_ids}")
    
    # Create session
    import uuid
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    
    db_session = models.Session(
        session_id=session_id,
        request_id=request_id,
        candidates=agent_ids,
        log=[]
    )
    db.add(db_session)
    db.commit()
    
    return {
        "session_id": session_id,
        "request_id": request_id,
        "candidates": agent_ids,
        "websocket_url": f"ws://localhost:8000/ws/session/{session_id}"
    }

@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session details and negotiation log."""
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "request_id": session.request_id,
        "candidates": session.candidates,
        "log": session.log or []
    }

@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    """List all negotiation sessions."""
    sessions = db.query(models.Session).all()
    return [{
        "session_id": session.session_id,
        "request_id": session.request_id,
        "candidates": session.candidates,
        "log_count": len(session.log) if session.log else 0
    } for session in sessions]
