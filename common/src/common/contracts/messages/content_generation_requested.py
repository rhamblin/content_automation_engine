from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class ContentGenerationRequested(IMessage):
    """Message contract for content generation requests"""

    tenant_id: str
    project_id: str
