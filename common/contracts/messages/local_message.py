from dataclasses import dataclass, asdict
from typing import Optional
import json

@dataclass
class LocalMessage:
    """Base class for test local message contracts"""
    message: str

    @classmethod
    def message_name(cls) -> str:
        return "local_message"
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LocalMessage':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))