# Author: diegomendez40 [Diego Méndez Romero - diegomendez40@gmail.com]
# Date: 16.06.24
# Description: Unit tests for AutonomousAgents.

import asyncio
import unittest
import io
from unittest.mock import AsyncMock, patch
from src.agent.agent import AutonomousAgent, random_message_generator

class TestAutonomousAgent(unittest.TestCase):
    def setUp(self):
        self.agent = AutonomousAgent("Test Agent")

    def test_init(self):
        self.assertEqual(self.agent.name, "Test Agent")
        self.assertIsInstance(self.agent.inbox, asyncio.Queue)
        self.assertEqual(self.agent.handlers, {})
        self.assertTrue(self.agent.running)
        self.assertEqual(self.agent.tasks, [])

    def test_register_handler(self):
        async def test_handler(message):
            pass

        self.agent.register_handler(test_handler)
        self.assertEqual(self.agent.handlers["default"], test_handler)

        with self.assertRaises(ValueError):
            self.agent.register_handler(lambda x: x)

    def test_register_behaviour(self):
        async def test_behaviour(agent):
            agent.behaviour_executed = True

        async def run_test():
            self.agent.behaviour_executed = False
            interval = 0.1
            
            # Register the test behaviour defined above
            await self.agent.register_behaviour(interval, test_behaviour)
            
            # Briefly wait so behaviour can execute
            await asyncio.sleep(0.2)
            
            # Check behaviour executed
            self.assertTrue(self.agent.behaviour_executed)
            
            # Reset status, check if it executes again
            self.agent.behaviour_executed = False
            await asyncio.sleep(0.2)
            self.assertTrue(self.agent.behaviour_executed)
            
            # Detener y cancelar todas las tareas
            await self.agent.stop()
            for task in self.agent.tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        asyncio.run(run_test())

    def test_consume_messages(self):
        async def test_handler(message):
            self.processed_message = message

        self.agent.register_handler(test_handler)

        async def run_test():
            self.processed_message = None
            consume_task = asyncio.create_task(self.agent.consume_messages())
            
            # Send message to inbox
            await self.agent.inbox.put("flamenco witches")
            
            # Briefly wait for message to be processed
            await asyncio.sleep(0.1)
            
            # Check message was processed
            self.assertEqual(self.processed_message, "flamenco witches")
            
            # Stop and cancel consume_task
            self.agent.running = False
            consume_task.cancel()
            try:
                await consume_task
            except asyncio.CancelledError:
                pass

        asyncio.run(run_test())

    def test_stop(self):
        async def test_stop():
            task = asyncio.create_task(asyncio.sleep(0))
            self.agent.tasks.append(task)

            await self.agent.stop()

            self.assertFalse(self.agent.running)
            self.assertTrue(task.cancelled())

        asyncio.run(test_stop())

class TestRandomMessageGenerator(unittest.TestCase):
    def setUp(self):
        # Crear un agente con un atributo sent_messages para pruebas
        self.agent = AutonomousAgent("Test Agent", sent_messages=[])
        self.receiver = AutonomousAgent("Receiver")
        self.agent.outbox = self.receiver.inbox

    def test_random_message_generator(self):
        async def run_test():

            # Ejecutar random_message_generator
            await random_message_generator(self.agent)
            
            # Verificar que el mensaje fue colocado en la outbox
            outbox_message = await self.agent.outbox.get()
            self.assertIn(outbox_message, self.agent.sent_messages)
            
            # Verificar que el mensaje se encuentra en sent_messages
            self.assertEqual(len(self.agent.sent_messages), 1)
            
            # Verificar el manejo de la excepción al poner mensajes en la outbox
            with patch('asyncio.Queue.put', new_callable=AsyncMock) as mock_put, \
                patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                mock_put.side_effect = Exception("Queue error")
                
                # Reiniciar sent_messages para la nueva prueba
                self.agent.sent_messages = []
                
                await random_message_generator(self.agent)
                
                # Verificar que no se añadió ningún mensaje a sent_messages
                self.assertEqual(len(self.agent.sent_messages), 0)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()