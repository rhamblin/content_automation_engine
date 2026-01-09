from dataclasses import dataclass, asdict
import json


@dataclass
class ContentReadyForPublication:
    """Message contract for content ready for publication"""
    content_id: str
    channel_key: str

    @classmethod
    def message_name(self) -> str:
        return "content_ready_for_publication"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'ContentReadyForPublication':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
