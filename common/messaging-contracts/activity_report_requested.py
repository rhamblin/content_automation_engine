from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class ActivityReportRequested:
    """Message contract for activity report requests"""
    schedule_id: str
    schedule_type: str
    scope_type: str
    scope_id: str
    triggered_at: str
    report_format: Optional[str] = None

    @classmethod
    def message_name(self) -> str:
        return "activity_report_requested"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'ActivityReportRequested':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
