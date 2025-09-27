import random
from typing import Dict, Any

def simple_policy(profile: Dict[str, Any], incoming_offer: Dict[str, Any]) -> str:
    """Simple rule-based policy for agent decision making."""
    service = incoming_offer.get("offer", {}).get("service", "unknown")
    
    # Check if we provide this service
    if service not in profile.get("services", []):
        return "reject"
    
    # Get our pricing for this service
    if "pricing" not in profile or service not in profile["pricing"]:
        return "reject"
    
    our_pricing = profile["pricing"][service]
    our_min = our_pricing.get("min", 0)
    our_max = our_pricing.get("max", float('inf'))
    
    # Get the incoming offer price
    offer_price = incoming_offer.get("offer", {}).get("price", 0)
    
    # Decision logic
    if offer_price >= our_max:
        return "accept"  # Great deal!
    elif offer_price >= our_min:
        # Within our range, but maybe we can negotiate
        if random.random() < 0.7:  # 70% chance to accept
            return "accept"
        else:
            return "counter"
    else:
        # Below our minimum, counter offer
        return "counter"

def advanced_policy(profile: Dict[str, Any], incoming_offer: Dict[str, Any], negotiation_history: list) -> str:
    """More sophisticated policy considering negotiation history."""
    service = incoming_offer.get("offer", {}).get("service", "unknown")
    
    if service not in profile.get("services", []):
        return "reject"
    
    if "pricing" not in profile or service not in profile["pricing"]:
        return "reject"
    
    our_pricing = profile["pricing"][service]
    our_min = our_pricing.get("min", 0)
    our_max = our_pricing.get("max", float('inf'))
    offer_price = incoming_offer.get("offer", {}).get("price", 0)
    
    # Count how many rounds we've been negotiating
    our_offers = [msg for msg in negotiation_history 
                  if msg.get("from") == profile["agent_id"] and msg.get("type") == "offer"]
    
    # If we've made too many offers, be more likely to accept
    if len(our_offers) >= 3:
        if offer_price >= our_min:
            return "accept"
    
    # If the offer is very close to our max, accept
    if offer_price >= our_max * 0.9:
        return "accept"
    
    # If it's within our range, negotiate
    if offer_price >= our_min:
        # Be more aggressive in countering if we haven't made many offers
        if len(our_offers) < 2:
            return "counter"
        else:
            return "accept" if random.random() < 0.6 else "counter"
    
    # Below minimum, counter offer
    return "counter"

def generate_counter_offer(profile: Dict[str, Any], incoming_offer: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a counter offer based on our pricing."""
    service = incoming_offer.get("offer", {}).get("service", "unknown")
    
    if service not in profile.get("services", []):
        return None
    
    our_pricing = profile["pricing"][service]
    our_min = our_pricing.get("min", 0)
    our_max = our_pricing.get("max", float('inf'))
    
    # Generate a counter offer between our min and max
    # Slightly above our min to leave room for further negotiation
    counter_price = our_min + (our_max - our_min) * 0.3
    
    # Copy the incoming offer structure but with our price
    counter_offer = incoming_offer["offer"].copy()
    counter_offer["price"] = int(counter_price)
    
    return counter_offer
