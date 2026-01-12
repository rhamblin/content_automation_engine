from common.contracts import IMessage
from dataclasses import dataclass
from typing import Optional

@dataclass
class CollectAnalyticsRequested(IMessage):
    """Message contract for analytics collection requests"""

    schedule_id: str
    schedule_type: str
    scope_type: str
    scope_id: str
    triggered_at: str
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None