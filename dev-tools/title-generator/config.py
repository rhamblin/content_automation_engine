"""Config loader — reads JSON data file and validates against TitleGenRequest contract."""

import json
from pathlib import Path

from models import TitleGenRequest

VALID_STYLES = {"mixed", "clickbait", "professional", "casual", "seo"}


def load_request(path: Path) -> TitleGenRequest:
    """Load a JSON data file and return a validated TitleGenRequest."""
    raw = json.loads(path.read_text())

    for field in ("channel", "niche", "keyword"):
        if field not in raw:
            raise ValueError(f"data file missing required field: {field}")

    style = raw.get("style", "mixed")
    if style not in VALID_STYLES:
        raise ValueError(f"invalid style '{style}', must be one of {VALID_STYLES}")

    return TitleGenRequest(
        channel=raw["channel"],
        niche=raw["niche"],
        keyword=raw["keyword"],
        count=raw.get("count", 3),
        style=style,
    )
