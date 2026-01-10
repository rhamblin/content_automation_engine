from abc import ABC, abstractmethod

class IMessageConsumer(ABC):
    @abstractmethod
    def consume(self, topic: str) -> dict:
        """Consume a message from the specified topic"""
        pass