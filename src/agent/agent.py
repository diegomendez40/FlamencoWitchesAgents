# Author: diegomendez40 [Diego Méndez Romero - diegomendez40@gmail.com]
# Date: 16.06.24
# Description: This script defines an AutonomousAgent class which can register handlers,
#              behaviors, and process messages asynchronously.

import asyncio
import random

class AutonomousAgent:
    def __init__(self, name, outbox=None, sent_messages=None):
        """
        Initialize an AutonomousAgent.
        
        :param name: Name of the agent
        :param outbox: Optional outbox queue for sending messages e.g. to other agents
        :param sent_messages: List to store sent messages, primarily for testing
        """
        self.name = name
        self.inbox = asyncio.Queue()
        self.outbox = outbox
        self.handlers = {}
        self.running = True
        self.tasks = []
        self.sent_messages = sent_messages  # For testing purposes only, not used in production

    def register_handler(self, handler, handler_key="default"):
        """
        Register a message handler.
        
        :param handler: Coroutine function to handle incoming messages
        :param handler_key: Optional key to register multiple handlers
        :raises ValueError: If handler is not a coroutine function
        """
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("Handler must be a coroutine function")
        self.handlers[handler_key] = handler

    async def register_behaviour(self, interval, behaviour):
        """
        Register a behavior to be run at a specified interval.
        
        :param interval: Time interval between behavior executions
        :param behaviour: Coroutine function to be executed at each interval
        """
        async def run_behaviour():
            while self.running:
                await asyncio.sleep(interval)
                try:
                    await behaviour(self)
                except Exception as e:
                    print(f"Error in behaviour: {e}")
        
        task = asyncio.create_task(run_behaviour())
        self.tasks.append(task)

    async def consume_messages(self):
        """
        Consume and process messages from the inbox queue.
        """
        while self.running:
            try:
                message = await self.inbox.get()
                if "default" in self.handlers:
                    await self.handlers["default"](message)
                self.inbox.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing message: {e}")

    async def stop(self):
        """
        Stop the agent, canceling all tasks and ensuring all messages are processed.
        """
        self.running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        await self.inbox.join()
        # No need to join outbox since it is part of another agent

async def message_handler(message):
    """
    Example message handler.
    
    :param message: Message to be handled
    """
    if "hello" in message:
        print(f"Handler received message: {message}")

async def random_message_generator(agent):
    """
    Generate random messages and put them in the agent's outbox.
    
    :param agent: Instance of AutonomousAgent
    """
    words = ["hello", "sun", "witches", "spain", "moon", "flamenco", "sky", "ocean", "universe", "human"]
    message = f"{random.choice(words)} {random.choice(words)}"
    try:
        if agent.outbox is not None:
            await agent.outbox.put(message)
        # For testing purposes only
        if agent.sent_messages is not None:
            agent.sent_messages.append(message)
    except Exception as e:
        print(f"Error putting message in outbox: {e}")