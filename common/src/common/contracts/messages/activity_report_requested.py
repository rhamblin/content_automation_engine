from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class ActivityReportRequested(IMessage):
    """Message contract for activity report requests"""

    tenant_id: str
