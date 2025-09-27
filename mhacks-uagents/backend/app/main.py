from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import db, models, registry, matchmaker, broker, contracts

app = FastAPI(
    title="Multi-Agent Negotiation System",
    description="A system for autonomous agent negotiation and contract formation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
models.Base.metadata.create_all(bind=db.engine)

# Include routers
app.include_router(registry.router, prefix="/api/v1", tags=["registry"])
app.include_router(matchmaker.router, prefix="/api/v1", tags=["matchmaker"])
app.include_router(broker.router, prefix="/api/v1", tags=["broker"])
app.include_router(contracts.router, prefix="/api/v1", tags=["contracts"])

@app.get("/")
def read_root():
    return {
        "message": "Multi-Agent Negotiation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws/session/{session_id}"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
