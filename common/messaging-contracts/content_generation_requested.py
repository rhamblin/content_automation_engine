from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json


@dataclass
class ContentGenerationRequested:
    """Message contract for content generation requests"""
    job_id: str
    project_id: str
    integration_profile_id: str
    data: Optional[Dict[str, Any]] = None

    @classmethod
    def message_name(cls) -> str:
        return "content_generation_requested"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'ContentGenerationRequested':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
