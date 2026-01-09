from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class PromotionOrchestratorRequested:
    """Message contract for promotion orchestrator requests"""
    schedule_id: str
    schedule_type: str
    scope_type: str
    scope_id: str
    triggered_at: str
    campaign_id: Optional[str] = None
    budget: Optional[float] = None

    @classmethod
    def message_name(cls) -> str:
        return "promotion_orchestrator_requested"

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'PromotionOrchestratorRequested':
        """Deserialize from JSON string"""
        return cls(**json.loads(json_str))
