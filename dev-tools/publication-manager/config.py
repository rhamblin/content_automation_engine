"""Config loader — reads JSON data file and validates against PublicationRequest contract."""

import json
from pathlib import Path

from models import PublicationRequest

VALID_COMMANDS = {"evaluate"}


def load_request(path: Path) -> PublicationRequest:
    """Load a JSON data file and return a validated PublicationRequest."""
    raw = json.loads(path.read_text())

    command = raw.get("command", "evaluate")
    if command not in VALID_COMMANDS:
        raise ValueError(f"invalid command '{command}', must be one of {VALID_COMMANDS}")

    return PublicationRequest(
        command=command,
        days=raw.get("days", 7),
        limit=raw.get("limit"),
        min_impressions=raw.get("min_impressions", 500),
        high_ctr=raw.get("high_ctr", 1.5),
        low_ctr=raw.get("low_ctr", 0.5),
        high_save_rate=raw.get("high_save_rate", 2.0),
        low_save_rate=raw.get("low_save_rate", 0.5),
        actionable=raw.get("actionable", False),
        output_json=raw.get("output_json", False),
    )
