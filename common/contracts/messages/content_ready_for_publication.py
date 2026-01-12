from ..interfaces.message import IMessage
from dataclasses import dataclass

@dataclass
class ContentReadyForPublication(IMessage):
    """Message contract for content ready for publication"""

    content_id: str
    channel_key: str
