# LLM-Powered Negotiation System Guide

## 🧠 Overview

The Multi-Agent Negotiation System now features advanced LLM-powered negotiation capabilities that enable agents to make intelligent, context-aware decisions during contract negotiations. This system uses OpenAI's GPT models to analyze offers, consider agent profiles, and make strategic decisions.

## 🚀 Key Features

### 1. Intelligent Decision Making
- **Context Analysis**: Agents analyze their own profiles, incoming offers, and negotiation history
- **Strategic Reasoning**: Each decision is backed by detailed reasoning and analysis
- **Confidence Scoring**: Every decision includes a confidence level (0.0 to 1.0)

### 2. Adaptive Negotiation Strategies
- **Aggressive**: High-risk, high-reward approach for competitive situations
- **Collaborative**: Win-win approach focusing on mutual benefit
- **Competitive**: Strategic positioning to maximize agent value
- **Conservative**: Risk-averse approach for stable deals

### 3. Profile-Aware Negotiation
- **Pricing Analysis**: Intelligent analysis of pricing structures and market positioning
- **Risk Assessment**: Evaluation of risk tolerance based on agent attributes
- **Priority Alignment**: Decisions based on agent's key priorities and deal breakers

## 🔧 Technical Architecture

### Core Components

#### 1. LLMNegotiator Class
```python
class LLMNegotiator:
    - analyze_agent_profile()  # Extract negotiation preferences
    - calculate_offer_value()  # Score incoming offers
    - determine_strategy()     # Choose negotiation approach
    - analyze_negotiation()    # Main decision-making method
```

#### 2. NegotiationContext
```python
@dataclass
class NegotiationContext:
    agent_profile: Dict[str, Any]
    incoming_offer: Dict[str, Any]
    negotiation_history: List[Dict[str, Any]]
    session_info: Dict[str, Any]
    round_number: int
    time_remaining: Optional[int]
```

#### 3. NegotiationDecision
```python
@dataclass
class NegotiationDecision:
    action: str                    # "accept", "counter", "reject", "wait"
    confidence: float              # 0.0 to 1.0
    reasoning: str                 # Detailed explanation
    counter_offer: Optional[Dict]  # If countering
    strategy: NegotiationStrategy  # Strategy used
```

## 📊 Decision Process

### 1. Profile Analysis
The system analyzes agent profiles to extract:
- **Pricing Strategy**: Fixed, moderate, or flexible pricing
- **Risk Tolerance**: Low, medium, or high risk acceptance
- **Negotiation Style**: Competitive, collaborative, or conservative
- **Key Priorities**: What the agent values most
- **Deal Breakers**: What the agent cannot accept

### 2. Offer Evaluation
Each incoming offer is scored based on:
- **Price Compatibility**: How well the price fits the agent's range
- **Service Match**: Whether the agent can provide the service
- **Terms Alignment**: How well terms match agent preferences
- **Market Position**: Competitive positioning

### 3. Strategic Decision
The LLM considers:
- **Current Round**: Later rounds may require more decisive action
- **Offer Value**: High-value offers may warrant acceptance
- **Agent Priorities**: Alignment with key priorities
- **Negotiation History**: Patterns and previous interactions

## 🎯 Usage Examples

### Basic LLM Negotiation
```bash
# Set API key
export OPENAI_API_KEY="your-key-here"

# Start agent with LLM
python agents/agent_worker.py agents/sample_profile.json sess-123 --use-llm
```

### Rule-Based Fallback
```bash
# Force rule-based system
python agents/agent_worker.py agents/sample_profile.json sess-123 --no-llm
```

### Enhanced Demo
```bash
# Run comprehensive LLM demo
python demo_llm_negotiation.py
```

## 📈 Negotiation Strategies

### Aggressive Strategy
- **When**: High-value opportunities, competitive markets
- **Behavior**: Quick decisions, high counter-offers
- **Risk**: May miss good deals, may alienate partners

### Collaborative Strategy
- **When**: Long-term relationships, mutual benefit opportunities
- **Behavior**: Win-win solutions, transparent communication
- **Risk**: May accept suboptimal terms

### Competitive Strategy
- **When**: Market dominance, high-value contracts
- **Behavior**: Strategic positioning, calculated risks
- **Risk**: May prolong negotiations unnecessarily

### Conservative Strategy
- **When**: Risk-averse situations, stable markets
- **Behavior**: Careful analysis, safe decisions
- **Risk**: May miss opportunities

## 🔍 Monitoring and Debugging

### Log Analysis
The system provides detailed logs for each negotiation:
```json
{
  "type": "counter_offer",
  "from": "agent_id",
  "offer": {...},
  "reasoning": "Detailed explanation of decision",
  "confidence": 0.85,
  "strategy": "collaborative"
}
```

### Session Monitoring
```bash
# Check session status
curl http://localhost:8000/api/v1/sessions/{session_id}/status

# View negotiation log
curl http://localhost:8000/api/v1/sessions/{session_id}
```

## 🛠️ Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-4"  # Optional, defaults to gpt-4
```

### Agent Profile Enhancement
Enhanced profiles can include negotiation preferences:
```json
{
  "policy": {
    "negotiation_style": "collaborative",
    "key_priorities": ["quality", "reliability"],
    "deal_breakers": ["distance", "timing"],
    "risk_tolerance": "medium"
  }
}
```

## 🚨 Error Handling

### Fallback System
- **API Failures**: Automatic fallback to rule-based system
- **Invalid Responses**: JSON parsing errors trigger fallback
- **Timeout**: Long LLM calls timeout and fallback

### Logging
- **Debug Level**: Detailed negotiation reasoning
- **Error Level**: API failures and fallbacks
- **Info Level**: Decision summaries and confidence scores

## 📊 Performance Considerations

### LLM Costs
- **Token Usage**: Each negotiation round uses ~500-1000 tokens
- **Cost Optimization**: Caching and efficient prompting
- **Fallback**: Rule-based system for cost control

### Response Times
- **LLM Calls**: 1-3 seconds per decision
- **Fallback**: <100ms per decision
- **Caching**: Profile analysis cached for session duration

## 🔮 Future Enhancements

### Planned Features
1. **Multi-Model Support**: Integration with other LLM providers
2. **Learning System**: Agents learn from successful negotiations
3. **Market Analysis**: Real-time market condition integration
4. **Emotional Intelligence**: Understanding of negotiation dynamics
5. **Predictive Modeling**: Forecasting negotiation outcomes

### Extensibility
The system is designed for easy extension:
- **Custom Strategies**: Add new negotiation approaches
- **Profile Analysis**: Enhance agent profile understanding
- **Decision Logic**: Modify decision-making algorithms
- **Integration**: Connect with external data sources

## 🎯 Best Practices

### Agent Profile Design
1. **Clear Priorities**: Define what matters most to the agent
2. **Realistic Pricing**: Set achievable min/max price ranges
3. **Detailed Attributes**: Include experience, ratings, certifications
4. **Policy Clarity**: Define clear business rules and constraints

### Negotiation Monitoring
1. **Log Analysis**: Regularly review negotiation logs for insights
2. **Performance Tracking**: Monitor success rates and deal values
3. **Strategy Adjustment**: Modify strategies based on outcomes
4. **Profile Updates**: Refine agent profiles based on experience

### System Maintenance
1. **API Key Management**: Secure storage and rotation of API keys
2. **Fallback Testing**: Regular testing of rule-based fallback
3. **Performance Monitoring**: Track response times and costs
4. **Error Handling**: Monitor and address system errors

This LLM-powered negotiation system represents a significant advancement in autonomous agent capabilities, enabling sophisticated, context-aware decision making that can adapt to complex negotiation scenarios while maintaining transparency and reliability.
