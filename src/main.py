# Author: diegomendez40 [Diego Méndez Romero - diegomendez40@gmail.com]
# Date: 16.06.24
# Description: This script creates 2 agents that send each other randomly generated messages and filter them.

import asyncio
from agent.agent import AutonomousAgent, message_handler, random_message_generator

async def main():
    # Create two agents
    agent1 = AutonomousAgent("Agent1")
    agent2 = AutonomousAgent("Agent2")

    # Link agent1's outbox to agent2's inbox and vice versa
    agent1.outbox = agent2.inbox
    agent2.outbox = agent1.inbox

    # Register handler and behaviour
    agent1.register_handler(message_handler)
    agent2.register_handler(message_handler)

    await agent1.register_behaviour(2, random_message_generator)
    await agent2.register_behaviour(2, random_message_generator)

    # Start consuming messages
    consume_task1 = asyncio.create_task(agent1.consume_messages())
    consume_task2 = asyncio.create_task(agent2.consume_messages())

    # Run for a certain period to demonstrate
    await asyncio.sleep(30)
    await agent1.stop()
    await agent2.stop()

    # Cancel consuming tasks
    consume_task1.cancel()
    consume_task2.cancel()

    # Await the completion of all tasks
    await asyncio.gather(consume_task1, consume_task2, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())