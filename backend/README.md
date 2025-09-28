# DynamoDB Agent Matching Server

A Python Flask server that uses AWS DynamoDB to store agent profiles and conversations, with intelligent matching capabilities.

## Features

### Profile Management
- **POST /store** - Store agent profile data and get a unique ID
- **GET /retrieve/<id>** - Retrieve stored agent data by unique ID
- **GET /list** - List all stored agent IDs
- **POST /match** - Find matching agent based on description

### Conversation Management
- **POST /conversation** - Store conversation messages
- **GET /conversation/<id>** - Retrieve conversation by ID
- **GET /agent/<id>/conversations** - Get all conversations for an agent

### System
- **GET /health** - Health check endpoint
- DynamoDB-based storage with unique UUID identifiers
- Automatic metadata tracking (timestamp, ID)
- Error handling and logging
- Semantic matching using sentence transformers

## Prerequisites

- Python 3.7+
- AWS Account with DynamoDB access
- AWS CLI configured with appropriate credentials

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
aws configure
```

3. (Optional) Migrate existing JSON data:
```bash
python migrate_to_dynamodb.py
```

## Usage

### Quick Start
```bash
./start_server.sh
```

### Manual Start
1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python server.py
```

The server will start on `http://localhost:8080`

### Testing
Test the server:
```bash
python test_server.py
```

Test DynamoDB functionality:
```bash
python test_dynamodb.py
```

## API Endpoints

### Store Uagent Data
```bash
curl -X POST http://localhost:8080/store \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "job": "Software Developer",
    "averagePrice": 50.0,
    "tags": ["python", "web development", "api"],
    "location": ["San Francisco", "CA"],
    "description": "I specialize in Python web development and API design."
  }'
```

### Retrieve Uagent Data
```bash
curl http://localhost:8080/retrieve/<unique_id>
```

### Match Uagent
```bash
curl -X POST http://localhost:8080/match \
  -H "Content-Type: application/json" \
  -d '{"description": "I need help with Python web development"}'
```

### List All Stored Data
```bash
curl http://localhost:8080/list
```

### Store Conversation
```bash
curl -X POST http://localhost:8080/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-uuid-here",
    "message": "Hello! I need help with plumbing.",
    "sender": "user"
  }'
```

### Get Conversation
```bash
curl http://localhost:8080/conversation/<conversation_id>
```

### Get Agent Conversations
```bash
curl http://localhost:8080/agent/<agent_id>/conversations
```

### Health Check
```bash
curl http://localhost:8080/health
```

## Uagent Data Structure

Each uagent must include the following fields:
- `name` (str): Name of the uagent
- `address` (str): Unique address/identifier for the uagent
- `job` (str): Job title or profession
- `averagePrice` (float): Average price for services
- `tags` (List[str]): List of relevant tags/skills
- `location` (List[str]): Location information
- `description` (str): Detailed description of services

## Matching Algorithm

The matching system uses:
- Text similarity between request description and uagent description
- Tag matching for additional scoring
- Job title relevance for better matches
- Returns the uagent with the highest combined score

## Storage

Data is stored in AWS DynamoDB with the following structure:

### Tables
- **agent-profiles**: Stores agent profile information
- **agent-conversations**: Stores conversation messages

### DynamoDB Schema

#### agent-profiles Table
- **Primary Key**: `id` (String) - Unique agent identifier
- **Attributes**: name, address, job, averagePrice, tags, location, description, timestamp
- **Global Secondary Indexes**:
  - `job-index`: Query by job title
  - `location-index`: Query by location

#### agent-conversations Table
- **Primary Key**: `conversation_id` (String) - Unique conversation identifier
- **Sort Key**: `timestamp` (String) - Message timestamp
- **Attributes**: agent_id, message, sender
- **Global Secondary Index**:
  - `agent-conversations-index`: Query conversations by agent

## Example Response

When storing data, you'll receive:
```json
{
  "message": "JSON data stored successfully",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success"
}
```

When retrieving data, you'll receive:
```json
{
  "message": "JSON data retrieved successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00.000000",
    "data": {
      "name": "Alice Johnson",
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "job": "Software Developer",
      "averagePrice": 50.0,
      "tags": ["python", "web development", "api"],
      "location": ["San Francisco", "CA"],
      "description": "I specialize in Python web development and API design."
    }
  },
  "status": "success"
}
```

When matching uagents, you'll receive:
```json
{
  "message": "Match found successfully",
  "matched_address": "0x1234567890abcdef1234567890abcdef12345678",
  "match_score": 0.85,
  "matched_uagent": {
    "name": "Alice Johnson",
    "job": "Software Developer",
    "description": "I specialize in Python web development and API design.",
    "tags": ["python", "web development", "api"],
    "averagePrice": 50.0
  },
  "status": "success"
}
```
