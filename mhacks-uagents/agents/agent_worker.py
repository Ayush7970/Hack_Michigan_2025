import json
import asyncio
import websockets
import argparse
import sys
import os
from agent_policy import simple_policy, advanced_policy, generate_counter_offer
from llm_negotiator import NegotiationManager, NegotiationContext

class AgentWorker:
    def __init__(self, profile_path: str, session_id: str, server_url: str = "ws://localhost:8000", use_llm: bool = True):
        self.session_id = session_id
        self.server_url = server_url
        self.websocket = None
        self.profile = self.load_profile(profile_path)
        self.negotiation_history = []
        self.use_llm = use_llm
        self.negotiation_manager = NegotiationManager() if use_llm else None
        self.session_info = {}
        
    def load_profile(self, profile_path: str) -> dict:
        """Load agent profile from JSON file."""
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Profile file {profile_path} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in profile file {profile_path}")
            sys.exit(1)
    
    async def connect(self):
        """Connect to the negotiation session."""
        uri = f"{self.server_url}/ws/session/{self.session_id}"
        try:
            self.websocket = await websockets.connect(uri)
            print(f"[{self.profile['agent_id']}] Connected to session {self.session_id}")
            return True
        except Exception as e:
            print(f"[{self.profile['agent_id']}] Failed to connect: {e}")
            return False
    
    async def send_message(self, message: dict):
        """Send a message to the negotiation session."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            print(f"[{self.profile['agent_id']}] Sent: {message}")
    
    async def handle_message(self, message: dict):
        """Handle incoming messages from the negotiation session."""
        self.negotiation_history.append(message)
        print(f"[{self.profile['agent_id']}] Received: {message}")
        
        msg_type = message.get("type")
        
        if msg_type == "session_info":
            # Session started, store session info and make initial offer
            self.session_info = message
            await self.make_initial_offer()
            
        elif msg_type == "offer" and message.get("from") != self.profile["agent_id"]:
            # Another agent made an offer
            await self.handle_offer(message)
            
        elif msg_type == "contract_finalized":
            # Negotiation completed
            print(f"[{self.profile['agent_id']}] Contract finalized: {message.get('contract', {})}")
            
        elif msg_type == "accept":
            # Someone accepted an offer
            print(f"[{self.profile['agent_id']}] Someone accepted an offer")
    
    async def make_initial_offer(self):
        """Make the initial offer for our services."""
        # Find a service we provide
        services = self.profile.get("services", [])
        if not services:
            print(f"[{self.profile['agent_id']}] No services available")
            return
        
        service = services[0]  # Use first service
        
        # Get pricing for this service
        if "pricing" not in self.profile or service not in self.profile["pricing"]:
            print(f"[{self.profile['agent_id']}] No pricing for service {service}")
            return
        
        pricing = self.profile["pricing"][service]
        # Start with a price between min and max
        initial_price = pricing.get("min", 0) + (pricing.get("max", 100) - pricing.get("min", 0)) * 0.6
        
        offer = {
            "type": "offer",
            "from": self.profile["agent_id"],
            "offer": {
                "service": service,
                "price": int(initial_price),
                "start": "2025-01-28T10:00Z",
                "duration_mins": 60,
                "description": f"{service} service from {self.profile['agent_id']}"
            }
        }
        
        await self.send_message(offer)
    
    async def handle_offer(self, message: dict):
        """Handle an offer from another agent using intelligent negotiation."""
        try:
            if self.use_llm and self.negotiation_manager:
                # Use LLM-powered negotiation
                decision = await self.negotiation_manager.process_offer(
                    agent_profile=self.profile,
                    incoming_offer=message,
                    negotiation_history=self.negotiation_history,
                    session_info=self.session_info
                )
                
                print(f"[{self.profile['agent_id']}] LLM Decision: {decision.action} (confidence: {decision.confidence:.2f})")
                print(f"[{self.profile['agent_id']}] Reasoning: {decision.reasoning}")
                
                await self._execute_decision(decision, message)
            else:
                # Fallback to rule-based system
                action = advanced_policy(self.profile, message, self.negotiation_history)
                await self._execute_rule_based_decision(action, message)
                
        except Exception as e:
            print(f"[{self.profile['agent_id']}] Error in negotiation: {e}")
            # Fallback to simple policy
            action = simple_policy(self.profile, message)
            await self._execute_rule_based_decision(action, message)
    
    async def _execute_decision(self, decision, original_message: dict):
        """Execute LLM-based negotiation decision."""
        if decision.action == "accept":
            response = {
                "type": "accept",
                "from": self.profile["agent_id"],
                "original_offer": original_message,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence
            }
            await self.send_message(response)
            
        elif decision.action == "counter" and decision.counter_offer:
            response = {
                "type": "counter_offer",
                "from": self.profile["agent_id"],
                "offer": decision.counter_offer,
                "original_offer": original_message,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence
            }
            await self.send_message(response)
            
        elif decision.action == "reject":
            response = {
                "type": "reject",
                "from": self.profile["agent_id"],
                "reason": decision.reasoning,
                "original_offer": original_message,
                "confidence": decision.confidence
            }
            await self.send_message(response)
            
        elif decision.action == "wait":
            print(f"[{self.profile['agent_id']}] Waiting for better offer...")
            # Don't respond immediately, wait for next offer
    
    async def _execute_rule_based_decision(self, action: str, original_message: dict):
        """Execute rule-based negotiation decision."""
        if action == "accept":
            response = {
                "type": "accept",
                "from": self.profile["agent_id"],
                "original_offer": original_message
            }
            await self.send_message(response)
            
        elif action == "counter":
            counter_offer = generate_counter_offer(self.profile, original_message)
            if counter_offer:
                response = {
                    "type": "counter_offer",
                    "from": self.profile["agent_id"],
                    "offer": counter_offer,
                    "original_offer": original_message
                }
                await self.send_message(response)
            else:
                # Can't counter, reject
                response = {
                    "type": "reject",
                    "from": self.profile["agent_id"],
                    "reason": "Cannot provide this service",
                    "original_offer": original_message
                }
                await self.send_message(response)
                
        elif action == "reject":
            response = {
                "type": "reject",
                "from": self.profile["agent_id"],
                "reason": "Service not available or pricing incompatible",
                "original_offer": original_message
            }
            await self.send_message(response)
    
    async def run(self):
        """Main agent loop."""
        if not await self.connect():
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.profile['agent_id']}] Connection closed")
        except Exception as e:
            print(f"[{self.profile['agent_id']}] Error: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()

async def main():
    parser = argparse.ArgumentParser(description="Agent Worker for Multi-Agent Negotiation")
    parser.add_argument("profile", help="Path to agent profile JSON file")
    parser.add_argument("session_id", help="Negotiation session ID")
    parser.add_argument("--server", default="ws://localhost:8000", help="WebSocket server URL")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM-powered negotiation")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM and use rule-based system")
    
    args = parser.parse_args()
    
    # Determine if LLM should be used
    use_llm = args.use_llm or (not args.no_llm and os.getenv("GEMINI_API_KEY"))
    
    agent = AgentWorker(args.profile, args.session_id, args.server, use_llm=use_llm)
    
    if use_llm:
        print(f"[{agent.profile['agent_id']}] Starting with LLM-powered negotiation")
    else:
        print(f"[{agent.profile['agent_id']}] Starting with rule-based negotiation")
    
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
