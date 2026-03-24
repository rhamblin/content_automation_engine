"""Config loader — reads JSON data file, resolves niche config for prompts."""

import json
from dataclasses import dataclass
from pathlib import Path

from common.contracts.models import VisualStyle
from common.workflows.pin_maker import PinMakerRequest

VALID_LOCALES = {"en", "es", "sw"}

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"



@dataclass(frozen=True)
class PinMakerConfig:
    """Validated config from data file + tenant niche config."""

    request: PinMakerRequest
    persona_prompt: str
    audience_prompt: str
    channel_prompt: str
    brand_watermark: str
    keywords: list[dict]
    product: bool


def _resolve_prompt(value: str | None, base_dir: Path) -> str | None:
    """If value points to a file relative to base_dir, return its contents."""
    if value and (base_dir / value).is_file():
        return (base_dir / value).read_text()
    return value


def _load_styles(
    tenant: str, channel: str, *, include_inactive: bool = False
) -> dict[str, VisualStyle]:
    """Load style JSONs from config/tenants/{tenant}/styles/{channel}/.

    By default only active styles are returned.  Pass *include_inactive=True*
    to return all styles (used by the style editor).
    """
    styles_dir = CONFIG_ROOT / tenant / "styles" / channel
    if not styles_dir.exists():
        return {}
    styles: dict[str, VisualStyle] = {}
    for f in sorted(styles_dir.glob("*.json")):
        data = json.loads(f.read_text())
        if not include_inactive and data.get("active", True) is False:
            continue
        styles[data["name"]] = VisualStyle.from_dict(data)
    return styles


def load_request(path: Path, tenant: str = "dev-tenant", channel: str = "pinterest") -> PinMakerRequest:
    """Load a JSON data file and return a validated PinMakerRequest."""
    raw = json.loads(path.read_text())

    if "output_folder" not in raw or not raw["output_folder"]:
        raise ValueError("'output_folder' is required in the data file")

    locale = raw.get("locale", "en")
    if locale not in VALID_LOCALES:
        raise ValueError(f"invalid locale '{locale}', must be one of {VALID_LOCALES}")

    all_styles = _load_styles(tenant, channel)
    raw_styles = raw.get("styles", raw.get("style"))  # back-compat: accept old "style" key
    if isinstance(raw_styles, str):
        raw_styles = [raw_styles]
    if raw_styles is not None:
        for s in raw_styles:
            if s not in all_styles:
                raise ValueError(f"unknown style '{s}', available: {list(all_styles.keys())}")

    return PinMakerRequest(
        output_folder=raw["output_folder"],
        niche=raw.get("niche", "food"),
        locale=locale,
        styles=raw_styles,
    )


def load_config(path: Path, tenant: str = "dev-tenant") -> PinMakerConfig:
    """Load a JSON data file, resolve niche config, return validated config."""
    raw = json.loads(path.read_text())
    niche_name = raw.get("niche", "food")

    niche_dir = CONFIG_ROOT / tenant / "niches" / niche_name
    niche_json = niche_dir / f"{niche_name}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())

    # Read keywords from niche config, filter out disabled
    all_keywords = niche_data.get("keywords", [])
    active_keywords = [kw for kw in all_keywords if kw.get("active", True) is not False]
    if not active_keywords:
        raise ValueError(
            f"No active keywords in niche config '{niche_name}'. "
            "All keywords are disabled or the keywords list is empty."
        )

    persona_prompt = _resolve_prompt(niche_data.get("persona_prompt"), niche_dir) or ""
    audience_prompt = _resolve_prompt(niche_data.get("audience_prompt"), niche_dir) or ""
    channel_prompts = niche_data.get("channel_prompts", {})
    channel_prompt = _resolve_prompt(channel_prompts.get("pinterest"), niche_dir) or ""

    request = load_request(path, tenant)

    return PinMakerConfig(
        request=request,
        persona_prompt=persona_prompt,
        audience_prompt=audience_prompt,
        channel_prompt=channel_prompt,
        brand_watermark=niche_data.get("brand_watermark", ""),
        keywords=active_keywords,
        product=bool(niche_data.get("product", False)),
    )


def load_styles(
    tenant: str = "dev-tenant",
    channel: str = "pinterest",
    *,
    include_inactive: bool = False,
) -> dict[str, VisualStyle]:
    """Public helper for orchestrator to load resolved VisualStyle objects."""
    return _load_styles(tenant, channel, include_inactive=include_inactive)
