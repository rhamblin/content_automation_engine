from abc import ABC, abstractmethod

class IMessageBroker(ABC):
    @abstractmethod
    def consume(self, topic: str) -> dict:
        """Consume a message from the specified topic"""
        pass

    @abstractmethod
    def publish(self, topic: str, payload: dict) -> None:
        """Publish a message to the specified topic"""
        pass