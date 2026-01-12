from common.contracts import IMessage
from dataclasses import dataclass
from typing import Optional

@dataclass
class ContentReadyForStyling(IMessage):
    """Message contract for content ready for styling"""

    content_id: str
    channel_key: str
    style_profile_id: Optional[str] = None