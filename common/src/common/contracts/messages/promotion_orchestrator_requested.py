from ..interfaces.message import IMessage
from dataclasses import dataclass
from typing import Optional


@dataclass(kw_only=True)
class PromotionOrchestratorRequested(IMessage):
    """Message contract for promotion orchestrator requests"""

    tenant_id: str
