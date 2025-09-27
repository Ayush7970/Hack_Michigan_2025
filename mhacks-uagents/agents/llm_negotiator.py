"""
Advanced LLM-powered negotiation system for autonomous agents.
This module provides intelligent negotiation capabilities using Google Gemini API.
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NegotiationStrategy(Enum):
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    COLLABORATIVE = "collaborative"
    COMPETITIVE = "competitive"

@dataclass
class NegotiationContext:
    """Context for the current negotiation round."""
    agent_profile: Dict[str, Any]
    incoming_offer: Dict[str, Any]
    negotiation_history: List[Dict[str, Any]]
    session_info: Dict[str, Any]
    round_number: int
    time_remaining: Optional[int] = None

@dataclass
class NegotiationDecision:
    """Result of negotiation analysis."""
    action: str  # "accept", "counter", "reject", "wait"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    counter_offer: Optional[Dict[str, Any]] = None
    strategy: Optional[NegotiationStrategy] = None

class LLMNegotiator:
    """Advanced negotiator using Google Gemini for intelligent decision making."""
    
    def __init__(self, gemini_api_key: str = None, model: str = "gemini-1.5-flash"):
        self.api_key = gemini_api_key or self._get_api_key()
        self.model = model
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        else:
            self.client = None
        
    def _get_api_key(self) -> Optional[str]:
        """Get Google Gemini API key from environment or config."""
        import os
        return os.getenv("GEMINI_API_KEY")
    
    def _analyze_agent_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent profile to extract negotiation preferences."""
        analysis = {
            "pricing_strategy": "unknown",
            "risk_tolerance": "medium",
            "negotiation_style": "collaborative",
            "key_priorities": [],
            "flexibility_factors": [],
            "deal_breakers": []
        }
        
        # Analyze pricing structure
        pricing = profile.get("pricing", {})
        if pricing:
            services = list(pricing.keys())
            price_ranges = [(p.get("min", 0), p.get("max", 0)) for p in pricing.values()]
            avg_range = sum((max_val - min_val) for min_val, max_val in price_ranges) / len(price_ranges) if price_ranges else 0
            
            if avg_range < 10:
                analysis["pricing_strategy"] = "fixed"
                analysis["risk_tolerance"] = "low"
            elif avg_range < 25:
                analysis["pricing_strategy"] = "moderate"
                analysis["risk_tolerance"] = "medium"
            else:
                analysis["pricing_strategy"] = "flexible"
                analysis["risk_tolerance"] = "high"
        
        # Analyze attributes for negotiation style
        attributes = profile.get("attributes", {})
        if attributes.get("experience_years", 0) > 5:
            analysis["negotiation_style"] = "competitive"
        elif attributes.get("eco_certified"):
            analysis["negotiation_style"] = "collaborative"
        
        # Extract key priorities
        if attributes.get("eco_certified"):
            analysis["key_priorities"].append("environmental_sustainability")
        if attributes.get("insurance"):
            analysis["key_priorities"].append("reliability")
        if attributes.get("licensed"):
            analysis["key_priorities"].append("professionalism")
        
        # Extract deal breakers from policy
        policy = profile.get("policy", {})
        if policy.get("max_distance_km", 0) < 10:
            analysis["deal_breakers"].append("distance")
        if policy.get("min_notice_hours", 0) > 24:
            analysis["deal_breakers"].append("timing")
        
        return analysis
    
    def _calculate_offer_value(self, offer: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate the value of an offer from the agent's perspective."""
        service = offer.get("service", "")
        price = offer.get("price", 0)
        
        if service not in profile.get("services", []):
            return 0.0
        
        pricing = profile.get("pricing", {}).get(service, {})
        min_price = pricing.get("min", 0)
        max_price = pricing.get("max", 100)
        
        if max_price == min_price:
            return 0.5  # Neutral if no range
        
        # Normalize price to 0-1 scale
        if price <= min_price:
            return 1.0  # Excellent deal
        elif price >= max_price:
            return 0.0  # Bad deal
        else:
            return 1.0 - ((price - min_price) / (max_price - min_price))
    
    def _determine_strategy(self, context: NegotiationContext) -> NegotiationStrategy:
        """Determine negotiation strategy based on context."""
        profile_analysis = self._analyze_agent_profile(context.agent_profile)
        
        # If we're in later rounds, be more aggressive
        if context.round_number > 3:
            return NegotiationStrategy.AGGRESSIVE
        
        # If the offer is very good, be collaborative
        offer_value = self._calculate_offer_value(context.incoming_offer.get("offer", {}), context.agent_profile)
        if offer_value > 0.8:
            return NegotiationStrategy.COLLABORATIVE
        
        # If we have high risk tolerance, be competitive
        if profile_analysis["risk_tolerance"] == "high":
            return NegotiationStrategy.COMPETITIVE
        
        # Default to collaborative
        return NegotiationStrategy.COLLABORATIVE
    
    async def _call_llm(self, prompt: str) -> str:
        """Make Gemini call for negotiation decision."""
        if not self.client:
            # Fallback to rule-based system if no API key
            return self._fallback_decision(prompt)
        
        try:
            # Prepare the full prompt for Gemini
            full_prompt = f"""You are an expert negotiator AI. Analyze the situation and provide a JSON response with your decision.

{prompt}

Please respond with valid JSON only, no additional text."""
            
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return self._fallback_decision(prompt)
    
    def _fallback_decision(self, prompt: str) -> str:
        """Fallback decision when LLM is not available."""
        # Simple rule-based fallback
        return json.dumps({
            "action": "counter",
            "confidence": 0.6,
            "reasoning": "Using rule-based fallback system",
            "strategy": "collaborative"
        })
    
    async def analyze_negotiation(self, context: NegotiationContext) -> NegotiationDecision:
        """Main method to analyze negotiation and make decision."""
        
        # Analyze agent profile
        profile_analysis = self._analyze_agent_profile(context.agent_profile)
        strategy = self._determine_strategy(context)
        
        # Calculate offer value
        offer_value = self._calculate_offer_value(context.incoming_offer.get("offer", {}), context.agent_profile)
        
        # Build context for LLM
        llm_prompt = self._build_llm_prompt(context, profile_analysis, offer_value, strategy)
        
        # Get LLM decision
        llm_response = await self._call_llm(llm_prompt)
        
        # Parse and validate response
        try:
            decision_data = json.loads(llm_response)
            return NegotiationDecision(
                action=decision_data.get("action", "counter"),
                confidence=decision_data.get("confidence", 0.5),
                reasoning=decision_data.get("reasoning", "No reasoning provided"),
                counter_offer=decision_data.get("counter_offer"),
                strategy=strategy
            )
        except json.JSONDecodeError:
            # Fallback if LLM response is not valid JSON
            return self._create_fallback_decision(context, offer_value, strategy)
    
    def _build_llm_prompt(self, context: NegotiationContext, profile_analysis: Dict, offer_value: float, strategy: NegotiationStrategy) -> str:
        """Build comprehensive prompt for LLM."""
        
        prompt = f"""
You are an autonomous agent negotiator. Analyze this negotiation situation and provide a JSON response.

AGENT PROFILE:
- ID: {context.agent_profile.get('agent_id', 'unknown')}
- Services: {context.agent_profile.get('services', [])}
- Pricing Strategy: {profile_analysis['pricing_strategy']}
- Risk Tolerance: {profile_analysis['risk_tolerance']}
- Negotiation Style: {profile_analysis['negotiation_style']}
- Key Priorities: {profile_analysis['key_priorities']}
- Deal Breakers: {profile_analysis['deal_breakers']}

INCOMING OFFER:
{json.dumps(context.incoming_offer, indent=2)}

NEGOTIATION CONTEXT:
- Round: {context.round_number}
- Offer Value Score: {offer_value:.2f} (0=bad, 1=excellent)
- Strategy: {strategy.value}
- History Length: {len(context.negotiation_history)}

NEGOTIATION HISTORY (last 3 rounds):
{json.dumps(context.negotiation_history[-3:], indent=2)}

DECISION CRITERIA:
1. Accept if offer value > 0.8 and aligns with priorities
2. Counter if offer value 0.3-0.8 and we can improve terms
3. Reject if offer value < 0.3 or violates deal breakers
4. Consider round number - be more decisive in later rounds

RESPOND WITH JSON:
{{
    "action": "accept|counter|reject|wait",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of decision",
    "counter_offer": {{"service": "...", "price": 0, "terms": "..."}} (if action is counter)
}}
"""
        return prompt
    
    def _create_fallback_decision(self, context: NegotiationContext, offer_value: float, strategy: NegotiationStrategy) -> NegotiationDecision:
        """Create fallback decision when LLM fails."""
        
        if offer_value > 0.8:
            return NegotiationDecision(
                action="accept",
                confidence=0.8,
                reasoning="Excellent offer value based on pricing analysis",
                strategy=strategy
            )
        elif offer_value > 0.3:
            return NegotiationDecision(
                action="counter",
                confidence=0.6,
                reasoning="Moderate offer value, attempting to improve terms",
                counter_offer=self._generate_counter_offer(context),
                strategy=strategy
            )
        else:
            return NegotiationDecision(
                action="reject",
                confidence=0.7,
                reasoning="Poor offer value, not worth pursuing",
                strategy=strategy
            )
    
    def _generate_counter_offer(self, context: NegotiationContext) -> Dict[str, Any]:
        """Generate a counter offer based on agent profile."""
        incoming_offer = context.incoming_offer.get("offer", {})
        service = incoming_offer.get("service", "")
        
        if service not in context.agent_profile.get("services", []):
            return None
        
        pricing = context.agent_profile["pricing"][service]
        min_price = pricing.get("min", 0)
        max_price = pricing.get("max", 100)
        
        # Generate counter offer between min and 70% of max
        counter_price = min_price + (max_price - min_price) * 0.7
        
        return {
            "service": service,
            "price": int(counter_price),
            "start": incoming_offer.get("start", "2025-01-28T10:00Z"),
            "duration_mins": incoming_offer.get("duration_mins", 60),
            "description": f"Counter offer from {context.agent_profile['agent_id']}"
        }

class NegotiationManager:
    """Manages negotiation sessions and agent interactions."""
    
    def __init__(self, gemini_api_key: str = None):
        self.negotiator = LLMNegotiator(gemini_api_key)
        self.active_sessions = {}
    
    async def process_offer(self, agent_profile: Dict[str, Any], incoming_offer: Dict[str, Any], 
                          negotiation_history: List[Dict[str, Any]], session_info: Dict[str, Any]) -> NegotiationDecision:
        """Process an incoming offer and return negotiation decision."""
        
        context = NegotiationContext(
            agent_profile=agent_profile,
            incoming_offer=incoming_offer,
            negotiation_history=negotiation_history,
            session_info=session_info,
            round_number=len([msg for msg in negotiation_history if msg.get("from") == agent_profile["agent_id"]])
        )
        
        return await self.negotiator.analyze_negotiation(context)
    
    def get_negotiation_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get negotiation statistics for an agent."""
        # This could track success rates, average deal values, etc.
        return {
            "agent_id": agent_id,
            "total_negotiations": 0,
            "success_rate": 0.0,
            "average_deal_value": 0.0
        }
