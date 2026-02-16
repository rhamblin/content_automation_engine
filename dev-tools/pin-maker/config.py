"""Config loader — reads JSON data file and validates against PinMakerRequest contract."""

import json
from pathlib import Path

from common.contracts.models import VisualStyle
from common.workflows.pin_maker import PinMakerRequest

VALID_LOCALES = {"en", "es", "sw"}

STYLES_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


def _load_styles(tenant: str, channel: str) -> dict[str, VisualStyle]:
    """Load all style JSONs from config/tenants/{tenant}/styles/{channel}/."""
    styles_dir = STYLES_ROOT / tenant / "styles" / channel
    if not styles_dir.exists():
        return {}
    styles: dict[str, VisualStyle] = {}
    for f in sorted(styles_dir.glob("*.json")):
        data = json.loads(f.read_text())
        styles[data["name"]] = VisualStyle.from_dict(data)
    return styles


def load_request(path: Path, tenant: str = "dev-tenant", channel: str = "pinterest") -> PinMakerRequest:
    """Load a JSON data file and return a validated PinMakerRequest."""
    raw = json.loads(path.read_text())

    if "input_folder" not in raw:
        raise ValueError("data file missing required field: input_folder")

    locale = raw.get("locale", "en")
    if locale not in VALID_LOCALES:
        raise ValueError(f"invalid locale '{locale}', must be one of {VALID_LOCALES}")

    styles = _load_styles(tenant, channel)
    style = raw.get("style")
    if style is not None and style not in styles:
        raise ValueError(f"unknown style '{style}', available: {list(styles.keys())}")

    return PinMakerRequest(
        input_folder=raw["input_folder"],
        niche=raw.get("niche", "food"),
        locale=locale,
        style=style,
    )


def load_styles(tenant: str = "dev-tenant", channel: str = "pinterest") -> dict[str, VisualStyle]:
    """Public helper for orchestrator to load resolved VisualStyle objects."""
    return _load_styles(tenant, channel)
