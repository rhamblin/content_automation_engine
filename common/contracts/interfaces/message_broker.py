from abc import ABC, abstractmethod
from typing import TypeVar
from common.contracts import IMessage

T = TypeVar('T', bound=IMessage)

class IMessageBroker(ABC):
    @abstractmethod
    def consume(self, topic: type[T]) -> T:
        """Consume a message from the specified topic"""
        pass

    @abstractmethod
    def publish(self, message: IMessage) -> None:
        """Publish a message to the specified topic"""
        pass