from abc import ABC, abstractmethod
import asyncio

class BaseBot(ABC):
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.status = "stopped"
        self.loop = asyncio.get_event_loop()

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    def get_status(self):
        return self.status

    async def send_message(self, target, message):
        print(f"{self.bot_id} sending to {target}: {message}")