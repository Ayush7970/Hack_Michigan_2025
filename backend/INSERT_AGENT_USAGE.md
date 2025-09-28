# Insert Agent Script Usage

## Overview
The `insert_agent.py` script allows you to easily insert agents into the uagent matching server.

## Usage

### 1. Interactive Mode
Run the script without arguments to enter interactive mode:

```bash
python3 insert_agent.py
```

This will prompt you for:
- Agent name
- Agent address
- Job title
- Average price
- Tags (comma-separated)
- Location (comma-separated)
- Description

### 2. JSON File Mode
Run the script with a JSON file containing agent data:

```bash
python3 insert_agent.py sample_agent.json
```

## Example JSON File
```json
{
  "name": "John Smith",
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "job": "Electrician",
  "averagePrice": 95.0,
  "tags": ["electrical", "wiring", "outlets", "lighting", "safety"],
  "location": ["Los Angeles", "CA"],
  "description": "Licensed electrician with 10 years of experience. Specializes in residential and commercial electrical work."
}
```

## Required Fields
- `name` (string): Name of the agent
- `address` (string): Unique address/identifier
- `job` (string): Job title or profession
- `averagePrice` (number): Average price for services
- `tags` (array): List of relevant skills/tags
- `location` (array): Location information
- `description` (string): Detailed service description

## Examples

### Insert a Plumber
```bash
python3 insert_agent.py
# Follow prompts to enter plumber data
```

### Insert from JSON File
```bash
python3 insert_agent.py sample_agent.json
```

## Prerequisites
- Server must be running on `http://localhost:8080`
- Python 3 with `requests` library installed
- Valid agent data in the correct format

## Error Handling
The script will show clear error messages for:
- Server connection issues
- Invalid JSON format
- Missing required fields
- Server errors
