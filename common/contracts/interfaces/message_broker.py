from abc import ABC, abstractmethod
from common.contracts import IMessage

class IMessageBroker(ABC):
    @abstractmethod
    def consume(self, topic: type[IMessage]) -> IMessage:
        """Consume a message from the specified topic"""
        pass

    @abstractmethod
    def publish(self, message: IMessage) -> None:
        """Publish a message to the specified topic"""
        pass