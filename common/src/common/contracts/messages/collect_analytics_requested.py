from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class CollectAnalyticsRequested(IMessage):
    """Message contract for analytics collection requests"""

    tenant_id: str
