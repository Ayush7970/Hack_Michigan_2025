from sqlalchemy import Column, Integer, String, JSON, DateTime
from .db import Base
import datetime

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True)
    profile = Column(JSON)  # raw JSON blob

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    requester_id = Column(String)
    data = Column(JSON)  # raw JSON blob

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    request_id = Column(String)
    candidates = Column(JSON)  # list of agent IDs
    log = Column(JSON)  # negotiation log

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    contract = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
