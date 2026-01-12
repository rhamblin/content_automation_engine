from abc import ABC
from typing import Self
from dataclasses import asdict, is_dataclass
import re
import json

class IMessage(ABC):
    """Base class for messages"""

    def __init_subclass__(cls, **kwargs):
        """Called when a subclass is defined"""
        super().__init_subclass__(**kwargs)
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass. Add @dataclass decorator.")
        
    @classmethod
    def topic(cls) -> str:
        """Auto-convert ClassName to snake_case"""
        # ExampleClassName -> example_class_name
        name = re.sub('([A-Z])', r'_\1', cls.__name__).lower().lstrip('_')
        return name

    @classmethod
    def deserialize(cls, json_str: str) -> Self:
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
    
    def serialize(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))