from ..interfaces.message import IMessage
from dataclasses import dataclass

@dataclass
class LocalOutputMessage(IMessage):
    """Base class for test local message contracts. This topic is used for output messages from microservices."""

    message: str
