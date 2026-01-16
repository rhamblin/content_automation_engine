from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class LocalInputMessage(IMessage):
    """Base class for test local message contracts. This topic is used for input messages to microservices."""

    message: str
