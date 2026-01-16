import json
import re
import uuid
from abc import ABC
from dataclasses import asdict, dataclass, field
from typing import Optional, Self


@dataclass
class IMessage(ABC):
    """Base class for message contracts

    All subclasses MUST use @dataclass decorator.
    """

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    parent_id: Optional[str] = None

    def __post_init__(self):
        if self.correlation_id is None:
            self.correlation_id = self.job_id

    @classmethod
    def topic(cls) -> str:
        """Auto-convert ClassName to snake_case"""
        # ExampleClassName -> example_class_name
        name = re.sub("([A-Z])", r"_\1", cls.__name__).lower().lstrip("_")
        return name

    @classmethod
    def deserialize(cls, json_str: str) -> Self:
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))

    def serialize(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    def chain_from(self, parent: "IMessage") -> Self:
        """Link this message to a parent for tracing."""
        self.correlation_id = parent.correlation_id
        self.parent_id = parent.job_id
        return self
