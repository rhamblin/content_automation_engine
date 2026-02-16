"""Promotion-manager input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionRequest:
    """Defines what promotion-manager accepts."""

    command: str = "evaluate"  # list | evaluate | pause | start | budget
    days: int = 7
    target_cpc: float = 2.0
    high_ctr: float = 2.0
    low_ctr: float = 0.5
    min_impressions: int = 1000
    budget_increase: float = 25  # percentage
    execute: bool = False
    actionable: bool = False
    output_json: bool = False
    campaign_id: str | None = None  # for pause/start/budget commands
    budget_amount: float | None = None  # for budget command
    status_filter: str = "all"  # all | active | paused | archived
