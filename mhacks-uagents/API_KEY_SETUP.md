# API Key Setup Guide

## 🔑 Setting Up OpenAI API Key

To enable LLM-powered negotiation, you need to set up your OpenAI API key. Here are the different ways to do it:

### Method 1: Environment Variable (Recommended)

**For macOS/Linux:**
```bash
# Add to your ~/.zshrc or ~/.bashrc
export OPENAI_API_KEY="your-api-key-here"

# Or set it for the current session
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

**For Windows:**
```cmd
# Command Prompt
set OPENAI_API_KEY=your-api-key-here

# PowerShell
$env:OPENAI_API_KEY="your-api-key-here"
```

### Method 2: Create .env File

Create a `.env` file in the project root:

```bash
# In /Users/joshveergrewal/Desktop/Hack_Michigan_2025/mhacks-uagents/
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Method 3: Direct in Code (Not Recommended for Production)

You can also set it directly in the code, but this is not secure:

```python
# In llm_negotiator.py
self.api_key = "your-api-key-here"
```

## 🚀 Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

## ✅ Testing Your Setup

After setting up your API key, test it:

```bash
# Test if the key is set
echo $OPENAI_API_KEY

# Run the enhanced demo
python demo_llm_negotiation.py

# Or start an agent with LLM
python agents/agent_worker.py agents/sample_profile.json sess-123 --use-llm
```

## 🔧 Fallback System

If no API key is provided, the system automatically falls back to rule-based negotiation:

```bash
# This will work without an API key
python agents/agent_worker.py agents/sample_profile.json sess-123 --no-llm
```

## 💰 Cost Considerations

- **Token Usage**: Each negotiation round uses ~500-1000 tokens
- **Estimated Cost**: ~$0.01-0.05 per negotiation session
- **Fallback**: System automatically uses rule-based negotiation if API fails

## 🛡️ Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables for production**
3. **Rotate keys regularly**
4. **Monitor usage in OpenAI dashboard**

## 🐛 Troubleshooting

**Error: "No module named 'openai'"**
```bash
cd agents
pip install -r requirements.txt
```

**Error: "API key not found"**
```bash
export OPENAI_API_KEY="your-key-here"
```

**Error: "Invalid API key"**
- Check the key is correct
- Ensure it starts with `sk-`
- Verify it's active in OpenAI dashboard

**Error: "Rate limit exceeded"**
- Wait a few minutes
- Check your OpenAI usage limits
- Consider using a different model
