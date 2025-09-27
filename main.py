from uagents import Agent, Bureau, Context, Model
from datetime import datetime
 
 
class Message(Model):
    message: str
 
 
agent_2 = Agent(name="agent_2", seed="agent_2 recovery phrase", port=8000, endpoint="http://localhost:8000/submit")
 
ALICE_ADDRESS = 'agent1q0xdga2g7twurf3f9cp3h2lhxs59vhmajq5ph44xqxpmc6d8ugs766yhnql'
 
 
@agent_2.on_interval(period=3.0)
async def send_message(ctx: Context):
    await ctx.send(ALICE_ADDRESS, Message(message=f"hello {datetime.today().date()}"))
 
 
if __name__ == '__main__':
    agent_2.run()