from ..interfaces.message import IMessage
from dataclasses import dataclass
from typing import Optional


@dataclass(kw_only=True)
class CollectAnalyticsRequested(IMessage):
    """Message contract for analytics collection requests"""

    tenant_id: str
