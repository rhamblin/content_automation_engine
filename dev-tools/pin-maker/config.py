"""Config loader — reads JSON data file and validates against PinMakerRequest contract."""

import json
from pathlib import Path

from common.providers.distribution_channel.pinterest import STYLES

from models import PinMakerRequest

VALID_LOCALES = {"en", "es", "sw"}


def load_request(path: Path) -> PinMakerRequest:
    """Load a JSON data file and return a validated PinMakerRequest."""
    raw = json.loads(path.read_text())

    if "input_folder" not in raw:
        raise ValueError("data file missing required field: input_folder")

    locale = raw.get("locale", "en")
    if locale not in VALID_LOCALES:
        raise ValueError(f"invalid locale '{locale}', must be one of {VALID_LOCALES}")

    style = raw.get("style")
    if style is not None and style not in STYLES:
        raise ValueError(f"unknown style '{style}', available: {list(STYLES.keys())}")

    return PinMakerRequest(
        input_folder=raw["input_folder"],
        niche=raw.get("niche", "food"),
        locale=locale,
        style=style,
    )
