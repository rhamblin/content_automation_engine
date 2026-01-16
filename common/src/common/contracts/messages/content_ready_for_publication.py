from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class ContentReadyForPublication(IMessage):
    """Message contract for content ready for publication"""

    tenant_id: str
    keyword_id: str
    niche_id: str
    channel_id: str
    content_id: str
    rendered_image_id: str
