# Author: diegomendez40 [Diego Méndez Romero - diegomendez40@gmail.com]
# Date: 16.06.24
# Description: Integration tests for AutonomousAgents.


import unittest
import asyncio
from unittest.mock import patch
from io import StringIO
from src.agent.agent import (
    AutonomousAgent,
    random_message_generator,
    message_handler
)

class TestAutonomousAgentsIntegration(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.agent1 = AutonomousAgent("Agent1", sent_messages=[])
        self.agent2 = AutonomousAgent("Agent2", sent_messages=[])
        self.agent1.outbox = self.agent2.inbox
        self.agent2.outbox = self.agent1.inbox

    def tearDown(self):
        self.loop.run_until_complete(self.agent1.stop())
        self.loop.run_until_complete(self.agent2.stop())
        self.loop.run_until_complete(asyncio.sleep(0))
        self.loop.close()

    def test_agents_communication(self):
        async def run_test():
            self.agent1.register_handler(message_handler)
            self.agent2.register_handler(message_handler)

            behaviour_task1 = asyncio.create_task(self.agent1.register_behaviour(0.1, random_message_generator))
            behaviour_task2 = asyncio.create_task(self.agent2.register_behaviour(0.1, random_message_generator))

            consume_task1 = asyncio.create_task(self.agent1.consume_messages())
            consume_task2 = asyncio.create_task(self.agent2.consume_messages())

            self.agent1.tasks.extend([behaviour_task1, consume_task1])
            self.agent2.tasks.extend([behaviour_task2, consume_task2])

             # Capturamos la salida estándar mientras damos tiempo para ejecutar
            with patch('sys.stdout', new=StringIO()) as mock_stdout:
                await asyncio.sleep(3)
                await self.agent1.stop()
                await self.agent2.stop()

                behaviour_task1.cancel()
                behaviour_task2.cancel()
                consume_task1.cancel()
                consume_task2.cancel()

                await asyncio.gather(
                    behaviour_task1, behaviour_task2, 
                    consume_task1, consume_task2, 
                    return_exceptions=True
                )
       
            # Verificamos la salida estándar capturada
            output = mock_stdout.getvalue()
            print("Captured Output:\n", output)
            print("Agent1 Processed Messages:\n", self.agent1.sent_messages)
            print("Agent2 Processed Messages:\n", self.agent2.sent_messages)
            self.assertTrue(all(len(sent_messages) >= 25 for sent_messages in [self.agent1.sent_messages, self.agent2.sent_messages]))
            
            # Verificamos que los mensajes con "hello" de cada agente estén en la salida capturada
            for sent_messages in [self.agent1.sent_messages, self.agent2.sent_messages]:
                hello_messages = [msg for msg in sent_messages if "flamenco" in msg]
                for msg in hello_messages:
                    self.assertIn(f"Handler received message: {msg}", output)

        self.loop.run_until_complete(run_test())

if __name__ == '__main__':
    unittest.main()