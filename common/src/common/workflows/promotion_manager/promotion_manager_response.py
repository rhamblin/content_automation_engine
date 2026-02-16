"""Promotion-manager output contract."""

from dataclasses import dataclass, field


@dataclass
class CampaignInfo:
    """Campaign listing with metrics."""

    id: str
    name: str
    status: str
    daily_spend_cap: float
    lifetime_spend_cap: float
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0


@dataclass
class CampaignEvaluation:
    """Result of evaluating a single campaign."""

    campaign_id: str
    campaign_name: str
    action: str
    reason: str
    current_budget: float
    metrics: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)
