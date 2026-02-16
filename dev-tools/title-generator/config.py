"""Config loader — reads JSON data file, resolves niche config for prompts."""

import json
from dataclasses import dataclass
from pathlib import Path

from common.workflows.title_generator import TitleGenRequest

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class TitleGenConfig:
    """Validated config from data file + tenant niche config."""

    request: TitleGenRequest
    persona_prompt: str
    channel_prompt: str
    copy_style_prompt: str


def _resolve_prompt(value: str | None, base_dir: Path) -> str | None:
    """If value points to a file relative to base_dir, return its contents."""
    if value and (base_dir / value).is_file():
        return (base_dir / value).read_text()
    return value


def load_config(path: Path) -> TitleGenConfig:
    """Load a JSON data file, resolve niche config, return validated config."""
    raw = json.loads(path.read_text())

    for field in ("tenant", "channel", "niche", "keywords"):
        if field not in raw:
            raise ValueError(f"data file missing required field: {field}")

    keywords = raw["keywords"]
    if isinstance(keywords, str):
        keywords = [keywords]
    if not keywords:
        raise ValueError("keywords must not be empty")

    tenant = raw["tenant"]
    niche = raw["niche"]
    channel = raw["channel"]

    # --- resolve niche config ---
    niche_dir = CONFIG_ROOT / tenant / "niches" / niche
    niche_json = niche_dir / f"{niche}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())

    persona_prompt = _resolve_prompt(niche_data.get("persona_prompt"), niche_dir) or ""
    copy_style_prompt = _resolve_prompt(niche_data.get("copy_style_prompt"), niche_dir) or ""
    channel_prompts = niche_data.get("channel_prompts", {})
    channel_prompt = _resolve_prompt(channel_prompts.get(channel), niche_dir) or ""

    if not copy_style_prompt:
        raise ValueError(f"copy_style_prompt not configured for niche: {niche}")

    request = TitleGenRequest(
        tenant=tenant,
        channel=channel,
        niche=niche,
        keywords=tuple(keywords),
        count=raw.get("count", 1),
    )

    return TitleGenConfig(
        request=request,
        persona_prompt=persona_prompt,
        channel_prompt=channel_prompt,
        copy_style_prompt=copy_style_prompt,
    )
