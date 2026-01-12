from ..interfaces.message import IMessage
from dataclasses import dataclass
from typing import Optional

@dataclass
class PromotionOrchestratorRequested(IMessage):
    """Message contract for promotion orchestrator requests"""

    schedule_id: str
    schedule_type: str
    scope_type: str
    scope_id: str
    triggered_at: str
    campaign_id: Optional[str] = None
    budget: Optional[float] = None
