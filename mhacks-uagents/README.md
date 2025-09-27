# Multi-Agent Negotiation System (MHacks UAgents)

A production-quality MVP for autonomous agent negotiation and contract formation. This system enables multiple AI agents to negotiate service contracts in real-time using WebSocket communication.

## 🏗️ Architecture

- **Backend**: FastAPI with SQLAlchemy ORM
- **Database**: SQLite (easily configurable for PostgreSQL)
- **Communication**: WebSocket for real-time negotiation
- **Agents**: Autonomous Python workers with configurable policies
- **Matching**: Intelligent agent-request matching with scoring

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/session/{session_id}

### 3. Register Agents

```bash
# Register sample agents
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agents/sample_profile.json

curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agents/another_profile.json

curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agents/contractor_profile.json
```

### 4. Create a Service Request

```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-1",
    "requester_id": "user-99",
    "service": "lawn_mowing",
    "location": {"lat": 42.28, "lon": -83.74},
    "constraints": {"max_price": 45},
    "preferences": {"eco_friendly": true}
  }'
```

### 5. Find Matching Agents

```bash
curl http://localhost:8000/api/v1/match/req-1
```

### 6. Create Negotiation Session

```bash
curl -X POST http://localhost:8000/api/v1/match/req-1/create_session \
  -H "Content-Type: application/json" \
  -d '["lawn_care_pro", "eco_gardener"]'
```

### 7. Start Agent Workers

```bash
# Terminal 1 - Agent 1
cd agents
python agent_worker.py sample_profile.json sess-12345678

# Terminal 2 - Agent 2  
python agent_worker.py another_profile.json sess-12345678
```

## 📊 API Endpoints

### Registry
- `POST /api/v1/agents` - Register/update agent
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/requests` - Create service request
- `GET /api/v1/requests/{request_id}` - Get request details

### Matchmaker
- `GET /api/v1/match/{request_id}` - Find matching agents
- `POST /api/v1/match/{request_id}/create_session` - Create negotiation session
- `GET /api/v1/sessions/{session_id}` - Get session details

### Broker
- `WebSocket /ws/session/{session_id}` - Real-time negotiation
- `GET /api/v1/sessions/{session_id}/status` - Session status
- `POST /api/v1/sessions/{session_id}/start` - Start session

### Contracts
- `GET /api/v1/contracts` - List all contracts
- `GET /api/v1/contracts/{session_id}` - Get contract by session
- `GET /api/v1/contracts/stats` - Contract statistics

## 🤖 Agent System

### Agent Profiles

Agents are defined by JSON profiles containing:
- **Services**: List of services they provide
- **Pricing**: Min/max prices per service
- **Location**: Geographic coordinates
- **Availability**: Time slots when available
- **Attributes**: Experience, ratings, equipment
- **Policy**: Business rules and constraints

### Agent Policies

Three policy types are available:

1. **Simple Policy**: Basic rule-based decisions
2. **Advanced Policy**: Considers negotiation history and makes smarter decisions
3. **LLM-Powered Policy**: Uses Google Gemini models for intelligent, context-aware negotiation

### LLM-Powered Negotiation

The system now includes advanced AI-powered negotiation capabilities:

#### Features
- **Intelligent Decision Making**: Agents analyze offers using LLM reasoning
- **Strategic Tactics**: Adaptive strategies (aggressive, collaborative, competitive)
- **Context Awareness**: Considers agent profiles, negotiation history, and market conditions
- **Confidence Scoring**: Each decision includes confidence levels
- **Detailed Reasoning**: Transparent explanations for every negotiation decision

#### Setup
```bash
# Set your Google Gemini API key
export GEMINI_API_KEY="AIza-your-api-key-here"

# Start agents with LLM negotiation
python agents/agent_worker.py agents/sample_profile.json <session_id> --use-llm
```

#### Fallback System
If no API key is provided, the system automatically falls back to rule-based negotiation:
```bash
python agents/agent_worker.py agents/sample_profile.json <session_id> --no-llm
```

### Running Agents

```bash
python agent_worker.py <profile_file> <session_id> [--server <websocket_url>]
```

## 🔄 Complete Workflow

1. **Registration**: Agents register with their capabilities
2. **Request**: User creates a service request
3. **Matching**: System finds compatible agents
4. **Session**: Negotiation session is created
5. **Negotiation**: Agents exchange offers via WebSocket
6. **Contract**: When agreement is reached, contract is saved
7. **Completion**: All parties are notified of final contract

## 🛠️ Development

### Project Structure

```
mhacks-uagents/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── db.py            # Database setup
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── registry.py      # Agent/request APIs
│   │   ├── matchmaker.py    # Agent matching
│   │   ├── broker.py        # WebSocket broker
│   │   ├── contracts.py     # Contract management
│   │   └── utils.py         # Helper functions
│   └── requirements.txt
├── agents/
│   ├── agent_worker.py      # Agent worker
│   ├── agent_policy.py      # Decision policies
│   ├── sample_profile.json
│   ├── another_profile.json
│   └── contractor_profile.json
└── README.md
```

### Database Models

- **Agent**: Agent profiles and capabilities
- **Request**: Service requests from users
- **Session**: Negotiation sessions with participants
- **Contract**: Finalized agreements

### WebSocket Protocol

Messages are JSON with the following types:
- `session_info`: Initial session data
- `offer`: Service offer from agent
- `counter_offer`: Counter proposal
- `accept`: Accept an offer
- `reject`: Reject an offer
- `contract_finalized`: Final contract notification

## 🧪 Testing

### Manual Testing

1. Start the backend server
2. Register agents using the provided profiles
3. Create a service request
4. Find matching agents
5. Create a negotiation session
6. Start agent workers
7. Watch the negotiation unfold!

### Enhanced LLM Demo

For a comprehensive demonstration of the LLM-powered negotiation system:

```bash
# Run the enhanced demo
python demo_llm_negotiation.py

# This will:
# - Set up enhanced agent profiles
# - Create complex service requests
# - Demonstrate intelligent matching
# - Show LLM negotiation capabilities
```

### Example Test Script

```bash
#!/bin/bash
# Complete test flow

# Start server (in background)
uvicorn app.main:app --reload &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Register agents
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agents/sample_profile.json

# Create request
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-req", "requester_id": "test-user", "service": "lawn_mowing", "location": {"lat": 42.28, "lon": -83.74}, "constraints": {"max_price": 45}, "preferences": {}}'

# Find matches
curl http://localhost:8000/api/v1/match/test-req

# Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/v1/match/test-req/create_session \
  -H "Content-Type: application/json" \
  -d '["lawn_care_pro"]' | jq -r '.session_id')

echo "Session created: $SESSION_ID"

# Start agent
python agents/agent_worker.py agents/sample_profile.json $SESSION_ID

# Cleanup
kill $SERVER_PID
```

## 🚀 Production Considerations

### Database
- Switch from SQLite to PostgreSQL for production
- Add database migrations
- Implement connection pooling

### Security
- Add authentication and authorization
- Validate all inputs
- Rate limiting for APIs

### Scalability
- Redis for session management
- Load balancing for WebSocket connections
- Horizontal scaling of agent workers

### Monitoring
- Add logging and metrics
- Health checks and alerts
- Performance monitoring

## 📝 License

MIT License - feel free to use this for your hackathon project!

## 🤝 Contributing

This is a hackathon project, but contributions are welcome! Areas for improvement:
- More sophisticated matching algorithms
- Better agent policies
- Web UI for monitoring
- Mobile app for agents
- Integration with payment systems
