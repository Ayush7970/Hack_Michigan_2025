import math
from typing import List, Dict, Any

def calculate_distance(loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
    """Calculate distance between two locations using Haversine formula."""
    lat1, lon1 = loc1["lat"], loc1["lon"]
    lat2, lon2 = loc2["lat"], loc2["lon"]
    
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def score_agent(agent_profile: Dict[str, Any], request_data: Dict[str, Any]) -> float:
    """Score an agent based on how well they match a request."""
    score = 0.0
    
    # Service match (required)
    if request_data["service"] not in agent_profile["services"]:
        return 0.0  # Must provide the requested service
    
    score += 50.0  # Base score for service match
    
    # Location proximity
    if "location" in request_data and "location" in agent_profile:
        distance = calculate_distance(request_data["location"], agent_profile["location"])
        # Score decreases with distance (max 30 points, decreases by 1 per km)
        location_score = max(0, 30 - distance)
        score += location_score
    
    # Price compatibility
    if "constraints" in request_data and "max_price" in request_data["constraints"]:
        max_price = request_data["constraints"]["max_price"]
        if "pricing" in agent_profile and request_data["service"] in agent_profile["pricing"]:
            agent_min = agent_profile["pricing"][request_data["service"]].get("min", 0)
            agent_max = agent_profile["pricing"][request_data["service"]].get("max", float('inf'))
            
            if agent_max <= max_price:
                # Agent's max is within budget
                price_score = 20
            elif agent_min <= max_price:
                # Agent's min is within budget, but max isn't
                price_score = 10
            else:
                # Agent is too expensive
                price_score = 0
            
            score += price_score
    
    # Availability (simple check)
    if "availability" in agent_profile and agent_profile["availability"]:
        score += 10  # Bonus for having availability info
    
    return score

def rank_agents(agents: List[Dict[str, Any]], request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rank agents by their score for a given request."""
    scored_agents = []
    
    for agent in agents:
        score = score_agent(agent["profile"], request_data)
        if score > 0:  # Only include agents that can fulfill the request
            scored_agents.append({
                "agent_id": agent["agent_id"],
                "profile": agent["profile"],
                "score": score
            })
    
    # Sort by score (highest first)
    scored_agents.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_agents
