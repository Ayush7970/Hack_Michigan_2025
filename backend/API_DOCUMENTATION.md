# Uagent Matching Server API Documentation

## Overview
A Flask-based server that stores uagent profiles and provides intelligent matching based on service descriptions using semantic similarity.

**Base URL**: `https://literalistic-unadmitted-alton.ngrok-free.dev` (or `http://localhost:8080` for local)

---

## Endpoints

### 1. Store Uagent Data
**POST** `/store`

Stores a new uagent profile in the system.

#### Request Body
```json
{
  "name": "string",
  "address": "string", 
  "job": "string",
  "averagePrice": "number",
  "tags": ["string"],
  "location": ["string"],
  "description": "string"
}
```

#### Example Request
```bash
curl -X POST https://literalistic-unadmitted-alton.ngrok-free.dev/store \
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

#### Response
```json
{
  "message": "JSON data stored successfully",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success"
}
```

---

### 2. Find Matching Uagent
**POST** `/match`

Finds the best matching uagent based on a service description using semantic similarity.

#### Request Body
```json
{
  "description": "string"
}
```

#### Example Request
```bash
curl -X POST https://literalistic-unadmitted-alton.ngrok-free.dev/match \
  -H "Content-Type: application/json" \
  -d '{"description": "I need help with Python web development"}'
```

#### Response
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

---

### 3. Retrieve Uagent Data
**GET** `/retrieve/{id}`

Retrieves a specific uagent's data by their unique ID.

#### Example Request
```bash
curl https://literalistic-unadmitted-alton.ngrok-free.dev/retrieve/550e8400-e29b-41d4-a716-446655440000
```

#### Response
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

---

### 4. List All Uagents
**GET** `/list`

Returns a list of all stored uagent IDs.

#### Example Request
```bash
curl https://literalistic-unadmitted-alton.ngrok-free.dev/list
```

#### Response
```json
{
  "message": "Found 5 stored JSON files",
  "ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ],
  "status": "success"
}
```

---

### 5. Health Check
**GET** `/health`

Returns the server health status.

#### Example Request
```bash
curl https://literalistic-unadmitted-alton.ngrok-free.dev/health
```

#### Response
```json
{
  "message": "Server is running",
  "status": "healthy"
}
```

---

## Data Structure

### Uagent Profile
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the uagent |
| `address` | string | Yes | Unique address/identifier |
| `job` | string | Yes | Job title or profession |
| `averagePrice` | number | Yes | Average price for services |
| `tags` | array | Yes | List of relevant skills/tags |
| `location` | array | Yes | Location information |
| `description` | string | Yes | Detailed service description |

---

## Matching Algorithm

The server uses a **hybrid semantic matching approach**:

1. **Semantic Similarity**: Uses Sentence Transformers to understand meaning
2. **Enhanced Descriptions**: Combines job + description + tags for better matching
3. **Keyword Boosting**: Adds score boosts for profession-specific keywords
4. **Final Score**: `semantic_similarity + keyword_boosts`

### Supported Professions
- Plumber
- Carpenter  
- Mechanic
- Electrician
- Doctor
- Computer Technician
- HVAC Technician
- Appliance Technician

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Request must contain JSON data",
  "status": "error"
}
```

### 404 Not Found
```json
{
  "error": "No uagents available for matching",
  "status": "error"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error", 
  "status": "error"
}
```

---

## Data Persistence

- All data is stored in `json_storage/` directory
- Each uagent saved as `{unique_id}.json`
- Data persists between server restarts
- Includes metadata (ID, timestamp, original data)

---

## Examples

### Store a Plumber
```bash
curl -X POST https://literalistic-unadmitted-alton.ngrok-free.dev/store \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mike Rodriguez",
    "address": "0x1111111111111111111111111111111111111111",
    "job": "Plumber",
    "averagePrice": 85.0,
    "tags": ["plumbing", "repairs", "emergency", "drain cleaning"],
    "location": ["Chicago", "IL"],
    "description": "Licensed plumber with 15 years experience. Available 24/7 for urgent issues."
  }'
```

### Find a Plumber
```bash
curl -X POST https://literalistic-unadmitted-alton.ngrok-free.dev/match \
  -H "Content-Type: application/json" \
  -d '{"description": "I need a plumber to fix my broken sink and unclog the drain"}'
```

### Find a Computer Technician
```bash
curl -X POST https://literalistic-unadmitted-alton.ngrok-free.dev/match \
  -H "Content-Type: application/json" \
  -d '{"description": "My computer is running slow and I think it has a virus"}'
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created (for /store) |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
