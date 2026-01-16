from ..interfaces.message import IMessage
from dataclasses import dataclass
from typing import Optional


@dataclass(kw_only=True)
class ActivityReportRequested(IMessage):
    """Message contract for activity report requests"""

    tenant_id: str
