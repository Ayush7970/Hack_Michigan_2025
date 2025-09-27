from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from . import db, models
import json
import asyncio
from datetime import datetime

router = APIRouter()
sessions: Dict[str, Dict] = {}  # in-memory {session_id: {"clients":[], "log":[], "status": "active"}}

def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_session(self, message: str, session_id: str, exclude_websocket: WebSocket = None):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(message)
                    except:
                        # Remove dead connections
                        self.active_connections[session_id].remove(connection)

manager = ConnectionManager()

@router.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for agent negotiations."""
    # Accept connection first
    await websocket.accept()
    
    # Verify session exists
    db_session = db.SessionLocal()
    session = db_session.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        db_session.close()
        return
    
    await manager.connect(websocket, session_id)
    
    # Initialize session in memory if not exists
    if session_id not in sessions:
        sessions[session_id] = {
            "clients": [],
            "log": session.log or [],
            "status": "active",
            "request_id": session.request_id,
            "candidates": session.candidates
        }
    
    try:
        # Send session info to the connecting client
        session_info = {
            "type": "session_info",
            "session_id": session_id,
            "request_id": session.request_id,
            "candidates": session.candidates,
            "log": sessions[session_id]["log"]
        }
        await manager.send_personal_message(json.dumps(session_info), websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add timestamp
            message["timestamp"] = datetime.utcnow().isoformat()
            
            # Log the message
            sessions[session_id]["log"].append(message)
            
            # Save to database
            session.log = sessions[session_id]["log"]
            db_session.commit()
            
            # Handle different message types
            if message.get("type") == "offer":
                # Broadcast offer to all other participants
                await manager.broadcast_to_session(data, session_id, websocket)
                
            elif message.get("type") == "accept":
                # Contract finalized!
                contract = {
                    "winner": message["from"],
                    "session_id": session_id,
                    "request_id": session.request_id,
                    "details": message,
                    "finalized_at": message["timestamp"]
                }
                
                # Save contract to database
                db_contract = models.Contract(session_id=session_id, contract=contract)
                db_session.add(db_contract)
                db_session.commit()
                
                # Update session status
                sessions[session_id]["status"] = "completed"
                
                # Notify all participants
                final_message = {
                    "type": "contract_finalized",
                    "contract": contract,
                    "timestamp": message["timestamp"]
                }
                await manager.broadcast_to_session(json.dumps(final_message), session_id)
                
            elif message.get("type") == "reject":
                # Agent rejected the offer
                await manager.broadcast_to_session(data, session_id, websocket)
                
            elif message.get("type") == "counter_offer":
                # Counter offer
                await manager.broadcast_to_session(data, session_id, websocket)
                
            else:
                # Generic message - broadcast to all
                await manager.broadcast_to_session(data, session_id, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)
    finally:
        db_session.close()

@router.get("/sessions/{session_id}/status")
def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Get current status of a negotiation session."""
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    in_memory_status = sessions.get(session_id, {})
    
    return {
        "session_id": session_id,
        "request_id": session.request_id,
        "candidates": session.candidates,
        "status": in_memory_status.get("status", "unknown"),
        "active_connections": len(manager.active_connections.get(session_id, [])),
        "log_count": len(session.log) if session.log else 0
    }

@router.post("/sessions/{session_id}/start")
def start_negotiation(session_id: str, db: Session = Depends(get_db)):
    """Manually start a negotiation session."""
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Initialize session in memory
    sessions[session_id] = {
        "clients": [],
        "log": session.log or [],
        "status": "active",
        "request_id": session.request_id,
        "candidates": session.candidates
    }
    
    return {
        "status": "started",
        "session_id": session_id,
        "websocket_url": f"ws://localhost:8000/ws/session/{session_id}"
    }
