from ..interfaces.message import IMessage
from dataclasses import dataclass
from typing import Optional

@dataclass
class ActivityReportRequested(IMessage):
    """Message contract for activity report requests"""
    
    schedule_id: str
    schedule_type: str
    scope_type: str
    scope_id: str
    triggered_at: str
    report_format: Optional[str] = None
