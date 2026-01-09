from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class ContentReadyForStyling:
    """Message contract for content ready for styling"""
    content_id: str
    channel_key: str
    style_profile_id: Optional[str] = None

    @classmethod
    def message_name(self) -> str:
        return "content_ready_for_styling"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'ContentReadyForStyling':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
