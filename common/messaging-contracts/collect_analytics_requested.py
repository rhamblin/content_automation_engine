from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class CollectAnalyticsRequested:
    """Message contract for analytics collection requests"""
    schedule_id: str
    schedule_type: str
    scope_type: str
    scope_id: str
    triggered_at: str
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None

    @classmethod
    def message_name(cls) -> str:
        return "collect_analytics_requested"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'CollectAnalyticsRequested':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
