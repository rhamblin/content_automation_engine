"""Config loader — reads JSON data file, resolves niche config for prompts and keywords."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from common.workflows.title_generator import TitleGenRequest

logger = logging.getLogger(__name__)

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class TitleGenConfig:
    """Validated config from data file + tenant niche config."""

    request: TitleGenRequest
    persona_prompt: str
    channel_prompt: str
    audience_prompt: str
    keywords: list[dict]  # active keyword dicts from niche config (with blog_url)
    niche_title: str  # display title for hashtag generation


def _resolve_prompt(value: str | None, base_dir: Path) -> str | None:
    """If value points to a file relative to base_dir, return its contents."""
    if value and (base_dir / value).is_file():
        return (base_dir / value).read_text()
    return value


def load_config(path: Path) -> TitleGenConfig:
    """Load a JSON data file, resolve niche config, return validated config."""
    raw = json.loads(path.read_text())

    for field in ("tenant", "channel", "niche"):
        if field not in raw:
            raise ValueError(f"data file missing required field: {field}")

    tenant = raw["tenant"]
    niche = raw["niche"]
    channel = raw["channel"]

    # --- resolve niche config ---
    niche_dir = CONFIG_ROOT / tenant / "niches" / niche
    niche_json = niche_dir / f"{niche}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())

    # --- keywords from niche config ---
    all_keywords = niche_data.get("keywords", [])
    active_keywords = [kw for kw in all_keywords if kw.get("active", True) is not False]

    skipped = 0
    keywords_with_blog: list[dict] = []
    for kw in active_keywords:
        if not kw.get("blog_url"):
            logger.warning("Skipping keyword '%s' — no blog_url", kw.get("term", "?"))
            skipped += 1
            continue
        keywords_with_blog.append(kw)

    if skipped:
        logger.info("Skipped %d keyword(s) without blog_url", skipped)

    if not keywords_with_blog:
        raise ValueError(
            f"No usable keywords in niche config '{niche}'. "
            "All keywords are disabled or missing blog_url."
        )

    # --- prompts ---
    persona_prompt = _resolve_prompt(niche_data.get("persona_prompt"), niche_dir) or ""
    audience_prompt = _resolve_prompt(niche_data.get("audience_prompt"), niche_dir) or ""
    channel_prompts = niche_data.get("channel_prompts", {})
    channel_prompt = _resolve_prompt(channel_prompts.get(channel), niche_dir) or ""

    request = TitleGenRequest(
        tenant=tenant,
        channel=channel,
        niche=niche,
    )

    return TitleGenConfig(
        request=request,
        persona_prompt=persona_prompt,
        channel_prompt=channel_prompt,
        audience_prompt=audience_prompt,
        keywords=keywords_with_blog,
        niche_title=niche_data.get("title", niche),
    )
