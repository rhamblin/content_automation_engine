"""Config loader — reads JSON data file and validates against TitleGenRequest contract."""

import json
from pathlib import Path

from common.workflows.title_generator import TitleGenRequest

VALID_STYLES = {"mixed", "clickbait", "professional", "casual", "seo"}


def load_request(path: Path) -> TitleGenRequest:
    """Load a JSON data file and return a validated TitleGenRequest."""
    raw = json.loads(path.read_text())

    for field in ("channel", "niche", "keywords"):
        if field not in raw:
            raise ValueError(f"data file missing required field: {field}")

    keywords = raw["keywords"]
    if isinstance(keywords, str):
        keywords = [keywords]
    if not keywords:
        raise ValueError("keywords must not be empty")

    style = raw.get("style", "mixed")
    if style not in VALID_STYLES:
        raise ValueError(f"invalid style '{style}', must be one of {VALID_STYLES}")

    return TitleGenRequest(
        channel=raw["channel"],
        niche=raw["niche"],
        keywords=tuple(keywords),
        count=raw.get("count", 1),
        style=style,
    )
