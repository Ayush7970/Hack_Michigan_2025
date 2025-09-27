from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import db, models, schemas
from typing import List, Dict, Any

router = APIRouter()

def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@router.get("/contracts")
def list_contracts(db: Session = Depends(get_db)):
    """List all finalized contracts."""
    contracts = db.query(models.Contract).all()
    return [{
        "id": contract.id,
        "session_id": contract.session_id,
        "contract": contract.contract,
        "created_at": contract.created_at
    } for contract in contracts]

@router.get("/contracts/{session_id}")
def get_contract_by_session(session_id: str, db: Session = Depends(get_db)):
    """Get contract for a specific session."""
    contract = db.query(models.Contract).filter(models.Contract.session_id == session_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {
        "id": contract.id,
        "session_id": contract.session_id,
        "contract": contract.contract,
        "created_at": contract.created_at
    }

@router.post("/contracts")
def create_contract(contract: schemas.ContractSchema, db: Session = Depends(get_db)):
    """Manually create a contract (usually done by broker)."""
    db_contract = models.Contract(
        session_id=contract.session_id,
        contract=contract.contract
    )
    db.add(db_contract)
    db.commit()
    
    return {"status": "created", "contract_id": db_contract.id}

@router.get("/contracts/stats")
def get_contract_stats(db: Session = Depends(get_db)):
    """Get contract statistics."""
    total_contracts = db.query(models.Contract).count()
    
    # Get contracts by service type
    contracts = db.query(models.Contract).all()
    service_stats = {}
    
    for contract in contracts:
        service = contract.contract.get("service", "unknown")
        service_stats[service] = service_stats.get(service, 0) + 1
    
    return {
        "total_contracts": total_contracts,
        "by_service": service_stats
    }
