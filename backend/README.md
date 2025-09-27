# JSON Storage Server

A Python Flask server that accepts JSON data via POST requests and stores it uniquely for later retrieval.

## Features

- **POST /store** - Store uagent JSON data and get a unique ID
- **GET /retrieve/<id>** - Retrieve stored uagent data by unique ID
- **GET /list** - List all stored uagent IDs
- **POST /match** - Find matching uagent based on description
- **GET /health** - Health check endpoint
- File-based storage with unique UUID identifiers
- Automatic metadata tracking (timestamp, ID)
- Error handling and logging

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
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

JSON data is stored in the `json_storage/` directory with the following structure:
- Each file is named `<unique_id>.json`
- Files contain the original data plus metadata (ID, timestamp)
- Data persists between server restarts

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
