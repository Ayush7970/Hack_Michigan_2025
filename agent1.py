from uagents import Agent, Context, Model
 
 
class Message(Model):
    message: str
 
 
SEED_PHRASE = "My_seed_underscore_phase7970"
 
# Now your agent is ready to join the agentverse!
agent = Agent(
    name="agent_Ayush",
    seed=SEED_PHRASE,
    port=8000,
    mailbox=True,
    readme_path="README.md",
    publish_agent_details=True, 
    # endpoint="http://localhost:8000/submit"
)
 

@agent.on_message(model=Message)
async def got(ctx: Context, sender: str, msg: Message):

    ctx.logger.info(f"Got: {msg} (from {sender})")
     



# Copy the address shown below
print(f"Your agent's address is: {agent.address}")
 
if __name__ == "__main__":
    agent.run()