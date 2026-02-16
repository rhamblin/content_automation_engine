"""Config loader — reads JSON data file and validates against WpUploaderRequest contract."""

import json
from pathlib import Path

from models import WpUploaderRequest

VALID_STATUSES = {"draft", "publish"}


def load_request(path: Path) -> WpUploaderRequest:
    """Load a JSON data file and return a validated WpUploaderRequest."""
    raw = json.loads(path.read_text())

    if "topics_file" not in raw:
        raise ValueError("data file missing required field: topics_file")

    status = raw.get("status", "draft")
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status '{status}', must be one of {VALID_STATUSES}")

    return WpUploaderRequest(
        topics_file=raw["topics_file"],
        niche=raw.get("niche", "food"),
        status=status,
    )
