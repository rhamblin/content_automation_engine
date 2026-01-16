from dataclasses import dataclass

from ..interfaces.message import IMessage


@dataclass(kw_only=True)
class PromotionOrchestratorRequested(IMessage):
    """Message contract for promotion orchestrator requests"""

    tenant_id: str
