from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class LocalOutputMessage(IMessage):
    """Base class for test local message contracts. This topic is used for output messages from microservices."""

    message: str
