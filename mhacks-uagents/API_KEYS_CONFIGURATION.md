# 🔑 Complete API Keys Configuration Guide

This guide covers all API keys and configuration needed for the Multi-Agent Negotiation System.

## 📋 Required API Keys & Configuration

### 1. 🤖 Google Gemini API Key (Primary LLM)

**Purpose**: Powers the intelligent negotiation system for autonomous agents.

**How to get it:**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" 
4. Create a new API key
5. Copy the key (starts with `AIza...`)

**Where to put it:**

**Option A: Environment Variable (Recommended)**
```bash
# For current session
export GEMINI_API_KEY="AIza-your-actual-api-key-here"

# For permanent setup (add to ~/.zshrc)
echo 'export GEMINI_API_KEY="AIza-your-actual-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Option B: .env file**
```bash
# Create .env file in project root
echo "GEMINI_API_KEY=AIza-your-actual-api-key-here" > .env
```

**Option C: Direct in code (Not recommended for production)**
```python
# In llm_negotiator.py
self.api_key = "AIza-your-actual-api-key-here"
```

### 2. 🗄️ Database Configuration (Optional)

**Current Setup**: SQLite (no API key needed)
- **File**: `backend/app/db.py`
- **Database**: `mhacks.db` (created automatically)
- **No configuration needed**

**For Production (PostgreSQL)**:
```bash
# Environment variables
export DATABASE_URL="postgresql://username:password@localhost:5432/mhacks_db"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="mhacks_db"
export DB_USER="your_username"
export DB_PASSWORD="your_password"
```

### 3. 🌐 WebSocket Configuration (No API key needed)

**Current Setup**: Built-in WebSocket server
- **Port**: 8000 (configurable)
- **No external service needed**

### 4. 🔐 Authentication (Optional - for production)

**JWT Secret Key**:
```bash
export JWT_SECRET_KEY="your-super-secret-jwt-key-here"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRE_MINUTES="30"
```

**OAuth Providers** (if needed):
```bash
# Google OAuth
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"

# GitHub OAuth
export GITHUB_CLIENT_ID="your-github-client-id"
export GITHUB_CLIENT_SECRET="your-github-client-secret"
```

## 🚀 Quick Setup Commands

### Complete Setup Script
```bash
#!/bin/bash
# Complete setup for development

# 1. Set Gemini API key
export GEMINI_API_KEY="AIza-your-actual-api-key-here"

# 2. Install dependencies
cd backend && pip install -r requirements.txt
cd ../agents && pip install -r requirements.txt

# 3. Start backend server
cd ../backend && uvicorn app.main:app --reload &

# 4. Test the system
cd .. && python test_system.py

echo "✅ Setup complete! System is ready."
```

## 🔧 Configuration Files

### Environment Variables (.env)
Create a `.env` file in the project root:
```bash
# Primary LLM
GEMINI_API_KEY=AIza-your-actual-api-key-here

# Database (optional - defaults to SQLite)
# DATABASE_URL=postgresql://user:pass@localhost:5432/mhacks_db

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Authentication (optional)
# JWT_SECRET_KEY=your-jwt-secret
# JWT_ALGORITHM=HS256
# JWT_EXPIRE_MINUTES=30
```

### Backend Configuration (backend/app/config.py)
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mhacks.db")
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # Authentication (optional)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 30))

settings = Settings()
```

## 🧪 Testing Your Configuration

### Test Script
```bash
#!/bin/bash
# Test all configurations

echo "🧪 Testing API Key Configuration"
echo "================================"

# Test Gemini API Key
if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ GEMINI_API_KEY is set"
    python -c "import google.generativeai as genai; genai.configure(api_key='$GEMINI_API_KEY'); print('✅ Gemini API key is valid')"
else
    echo "❌ GEMINI_API_KEY is not set"
fi

# Test Database
echo "✅ Database: SQLite (no configuration needed)"

# Test Server
curl -s http://localhost:8000/health > /dev/null && echo "✅ Backend server is running" || echo "❌ Backend server is not running"

echo "================================"
echo "Configuration test complete!"
```

## 💰 Cost Considerations

### Gemini API Costs
- **Free Tier**: 15 requests per minute, 1M tokens per day
- **Paid Tier**: $0.0005 per 1K characters input, $0.0015 per 1K characters output
- **Estimated Cost**: ~$0.001-0.005 per negotiation session

### Database Costs
- **SQLite**: Free (local file)
- **PostgreSQL**: $0-50/month depending on provider

## 🛡️ Security Best Practices

### 1. Environment Variables
```bash
# Never commit API keys to version control
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

### 2. API Key Rotation
```bash
# Rotate keys regularly
# Set up monitoring for usage
# Use different keys for dev/prod
```

### 3. Access Control
```bash
# Restrict API key permissions
# Use least privilege principle
# Monitor API usage
```

## 🐛 Troubleshooting

### Common Issues

**1. "No module named 'google.generativeai'"**
```bash
pip install google-generativeai>=0.3.0
```

**2. "Invalid API key"**
```bash
# Check key format (should start with AIza)
echo $GEMINI_API_KEY
```

**3. "Rate limit exceeded"**
```bash
# Wait a few minutes
# Check your quota in Google AI Studio
```

**4. "Database connection failed"**
```bash
# Check DATABASE_URL format
# Ensure database server is running
```

## 📊 Monitoring & Logging

### API Usage Monitoring
```python
# Add to your code
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log API calls
logger.info(f"Gemini API call made: {tokens_used} tokens")
```

### Health Checks
```bash
# Check system health
curl http://localhost:8000/health

# Check API key status
python -c "import os; print('API Key set:', bool(os.getenv('GEMINI_API_KEY')))"
```

## 🚀 Production Deployment

### Environment Variables for Production
```bash
# Production .env
GEMINI_API_KEY=AIza-your-production-key
DATABASE_URL=postgresql://prod_user:secure_pass@db.example.com:5432/mhacks_prod
HOST=0.0.0.0
PORT=8000
DEBUG=false
JWT_SECRET_KEY=super-secure-production-key
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./data:/app/data
```

This comprehensive guide covers all the API keys and configuration needed for the Multi-Agent Negotiation System. The only required key is the Gemini API key for LLM functionality - everything else is optional or has sensible defaults.
