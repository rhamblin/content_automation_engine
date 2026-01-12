from common.contracts import IMessage
from dataclasses import dataclass, asdict

@dataclass
class LocalInputMessage(IMessage):
    """Base class for test local message contracts. This topic is used for input messages to microservices."""

    message: str
