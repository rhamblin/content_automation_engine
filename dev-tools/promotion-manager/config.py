"""Config loader — reads JSON data file and validates against PromotionRequest contract."""

import json
from pathlib import Path

from models import PromotionRequest

VALID_COMMANDS = {"list", "evaluate", "pause", "start", "budget"}
VALID_STATUSES = {"all", "active", "paused", "archived"}


def load_request(path: Path) -> PromotionRequest:
    """Load a JSON data file and return a validated PromotionRequest."""
    raw = json.loads(path.read_text())

    command = raw.get("command", "evaluate")
    if command not in VALID_COMMANDS:
        raise ValueError(f"invalid command '{command}', must be one of {VALID_COMMANDS}")

    if command in ("pause", "start", "budget") and not raw.get("campaign_id"):
        raise ValueError(f"command '{command}' requires campaign_id")

    if command == "budget" and raw.get("budget_amount") is None:
        raise ValueError("command 'budget' requires budget_amount")

    status_filter = raw.get("status_filter", "all")
    if status_filter not in VALID_STATUSES:
        raise ValueError(f"invalid status_filter '{status_filter}', must be one of {VALID_STATUSES}")

    return PromotionRequest(
        command=command,
        days=raw.get("days", 7),
        target_cpc=raw.get("target_cpc", 2.0),
        high_ctr=raw.get("high_ctr", 2.0),
        low_ctr=raw.get("low_ctr", 0.5),
        min_impressions=raw.get("min_impressions", 1000),
        budget_increase=raw.get("budget_increase", 25),
        execute=raw.get("execute", False),
        actionable=raw.get("actionable", False),
        output_json=raw.get("output_json", False),
        campaign_id=raw.get("campaign_id"),
        budget_amount=raw.get("budget_amount"),
        status_filter=status_filter,
    )
