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
    audience_prompt: str
    keyword_images: dict[str, str] | None = None  # keyword → image_path
    keyword_blog_urls: dict[str, str] | None = None    # keyword → url

    def __post_init__(self):
        if self.keyword_images is None:
            object.__setattr__(self, "keyword_images", {})
        if self.keyword_blog_urls is None:
            object.__setattr__(self, "keyword_blog_urls", {})


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

    raw_keywords = raw["keywords"]
    if isinstance(raw_keywords, str):
        raw_keywords = [raw_keywords]
    if not raw_keywords:
        raise ValueError("keywords must not be empty")

    # Support both plain strings and {"keyword": "...", "image_path": "...", "url": "..."} objects
    keywords: list[str] = []
    keyword_images: dict[str, str] = {}
    keyword_blog_urls: dict[str, str] = {}
    for entry in raw_keywords:
        if isinstance(entry, str):
            keywords.append(entry)
        elif isinstance(entry, dict):
            kw = entry.get("keyword", "")
            if not kw:
                raise ValueError("keyword object missing 'keyword' field")
            keywords.append(kw)
            if entry.get("image_path"):
                keyword_images[kw] = entry["image_path"]
            if entry.get("blog_url"):
                keyword_blog_urls[kw] = entry["blog_url"]
        else:
            raise ValueError(f"invalid keyword entry: {entry}")

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
    audience_prompt = _resolve_prompt(niche_data.get("audience_prompt"), niche_dir) or ""
    channel_prompts = niche_data.get("channel_prompts", {})
    channel_prompt = _resolve_prompt(channel_prompts.get(channel), niche_dir) or ""

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
        audience_prompt=audience_prompt,
        keyword_images=keyword_images,
        keyword_blog_urls=keyword_blog_urls,
    )
