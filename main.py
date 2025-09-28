from uagents import Agent, Bureau, Context, Model
from datetime import datetime
 
 
class Message(Model):
    message: str
 
 
agent_2 = Agent(name="agent_2", seed="agent_2 recovery phrase", port=8020, endpoint="http://localhost:8020/submit", mailbox=True)
 
ALICE_ADDRESS = 'agent1qvfnlashfjq67fsczqfs82mmnxu4ffu3xftsc75w62mfskhdnavtq0cknv9'
 
 
@agent_2.on_interval(period=3.0)
async def send_message(ctx: Context):
    await ctx.send(ALICE_ADDRESS, Message(message=f"hello {datetime.today().date()}"))
 
@agent_2.on_message(model=Message)
async def on_msg(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Got: {msg.message} (from {sender})")
    ctx.send(sender, Message(message=f"hi {datetime.today().date()}"))
 
if __name__ == '__main__':
    agent_2.run()