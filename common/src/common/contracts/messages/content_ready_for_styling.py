from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class ContentReadyForStyling(IMessage):
    """Message contract for content ready for styling"""

    tenant_id: str
    keyword_id: str
    niche_id: str
    channel_id: str
    content_id: str
    base_image_id: str
