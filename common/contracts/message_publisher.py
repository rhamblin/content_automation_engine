from abc import ABC, abstractmethod

class IMessagePublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, payload: dict) -> None:
        """Publish a message to the specified topic"""
        pass