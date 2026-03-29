"""Config loader — reads JSON data file, resolves keyword → reference_images."""

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class BgRemoverConfig:
    """Validated config from data file + tenant niche config."""

    keyword: str
    reference_images: str
    background_color: str
    output_folder: str


def load_config(path: Path) -> BgRemoverConfig:
    """Load JSON data file, resolve keyword to reference_images path."""
    raw = json.loads(path.read_text())

    tenant = raw.get("tenant", "dev-tenant")
    niche_name = raw.get("niche")
    keyword_term = raw.get("keyword")
    background_color = raw.get("background_color", "#FFFFFF")
    output_folder = raw.get("output_folder")

    if not niche_name:
        raise ValueError("'niche' is required in the data file")
    if not keyword_term:
        raise ValueError("'keyword' is required in the data file")
    if not output_folder:
        raise ValueError("'output_folder' is required in the data file")

    # Resolve niche config
    niche_dir = CONFIG_ROOT / tenant / "niches" / niche_name
    niche_json = niche_dir / f"{niche_name}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())

    # Find matching keyword
    all_keywords = niche_data.get("keywords", [])
    match = next(
        (kw for kw in all_keywords if kw.get("term") == keyword_term),
        None,
    )
    if match is None:
        available = [kw.get("term") for kw in all_keywords]
        raise ValueError(
            f"keyword '{keyword_term}' not found in niche '{niche_name}'. "
            f"Available: {available}"
        )

    reference_images = match.get("reference_images", "")
    if not reference_images:
        raise ValueError(
            f"keyword '{keyword_term}' has no 'reference_images' configured"
        )
    if not Path(reference_images).is_dir():
        raise ValueError(
            f"reference_images directory does not exist: {reference_images}"
        )

    return BgRemoverConfig(
        keyword=keyword_term,
        reference_images=reference_images,
        background_color=background_color,
        output_folder=output_folder,
    )
