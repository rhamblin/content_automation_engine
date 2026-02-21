"""Config loader — reads JSON data file, resolves niche prompts for WP uploader."""

import json
from dataclasses import dataclass
from pathlib import Path

from common.workflows.wp_uploader import WpUploaderRequest

VALID_STATUSES = {"draft", "publish"}

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class NichePrompts:
    """Resolved prompt strings from niche config."""

    channel_prompt: str
    persona_prompt: str
    copy_style_prompt: str
    audience_prompt: str


@dataclass(frozen=True)
class WpUploaderConfig:
    """Validated config from data file + tenant niche config."""

    request: WpUploaderRequest
    niche_prompts: NichePrompts


def _resolve_prompt(value: str | None, base_dir: Path) -> str | None:
    """If value points to a file relative to base_dir, return its contents."""
    if value and (base_dir / value).is_file():
        return (base_dir / value).read_text()
    return value


def load_request(path: Path, niche: str, status: str) -> WpUploaderRequest:
    """Load a JSON data file and return a validated WpUploaderRequest."""
    raw = json.loads(path.read_text())

    if "keywords" not in raw:
        raise ValueError("data file missing required field: keywords")

    keywords = raw["keywords"]
    if not keywords:
        raise ValueError("keywords must not be empty")

    return WpUploaderRequest(
        keywords=tuple(keywords),
        niche=niche,
        status=status,
    )


def load_config(path: Path, tenant: str = "dev-tenant") -> WpUploaderConfig:
    """Load a JSON data file, resolve niche config, return validated config."""
    raw = json.loads(path.read_text())
    niche_name = raw.get("niche")
    if not niche_name:
        raise ValueError("data file missing required field: niche")

    niche_dir = CONFIG_ROOT / tenant / "niches" / niche_name
    niche_json = niche_dir / f"{niche_name}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())

    persona_prompt = _resolve_prompt(niche_data.get("persona_prompt"), niche_dir) or ""
    copy_style_prompt = (
        _resolve_prompt(niche_data.get("copy_style_prompt"), niche_dir) or ""
    )
    audience_prompt = (
        _resolve_prompt(niche_data.get("audience_prompt"), niche_dir) or ""
    )
    channel_prompts = niche_data.get("channel_prompts", {})
    channel_prompt = _resolve_prompt(channel_prompts.get("wordpress"), niche_dir) or ""

    status = niche_data.get("status", "draft")
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status '{status}', must be one of {VALID_STATUSES}")

    request = load_request(niche_json, niche=niche_name, status=status)

    return WpUploaderConfig(
        request=request,
        niche_prompts=NichePrompts(
            channel_prompt=channel_prompt,
            persona_prompt=persona_prompt,
            copy_style_prompt=copy_style_prompt,
            audience_prompt=audience_prompt,
        ),
    )
