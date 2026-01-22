from abc import ABC, abstractmethod
from typing import TypeVar
from .message import IMessage

T = TypeVar('T', bound=IMessage)

class IMessageBroker(ABC):
    @abstractmethod
    async def consume(self, topic: type[T]) -> T:
        """Consume a message from the specified topic"""
        pass

    @abstractmethod
    async def publish(self, message: IMessage) -> None:
        """Publish a message to the specified topic"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the message broker connection"""
        pass