"""Config loader — reads JSON data file, resolves tenant LinkedIn config for news sources."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from common.workflows.linkedin.news_aggregator import (
    NewsAggregatorRequest,
    NewsSource,
)

logger = logging.getLogger(__name__)

CONFIG_ROOT = Path(__file__).parent.parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class NewsAggregatorConfig:
    """Validated config from data file + tenant LinkedIn config."""

    request: NewsAggregatorRequest
    tenant: str


def load_config(path: Path) -> NewsAggregatorConfig:
    """Load a JSON data file, resolve tenant LinkedIn config, return validated config."""
    raw = json.loads(path.read_text())

    if "tenant" not in raw:
        raise ValueError("data file missing required field: tenant")

    tenant = raw["tenant"]
    max_articles = raw.get("max_articles_per_source", 5)

    # --- resolve tenant LinkedIn config ---
    linkedin_dir = CONFIG_ROOT / tenant / "linkedin"
    linkedin_json = linkedin_dir / "linkedin.json"
    if not linkedin_json.exists():
        raise ValueError(f"LinkedIn config not found: {linkedin_json}")

    linkedin_data = json.loads(linkedin_json.read_text())

    # --- validate and parse news sources ---
    raw_sources = linkedin_data.get("news_sources", [])
    if not raw_sources:
        raise ValueError(
            f"No news_sources defined in {linkedin_json}. "
            "Add at least one source with 'name' and 'url' fields."
        )

    sources: list[NewsSource] = []
    for i, src in enumerate(raw_sources):
        name = src.get("name", "").strip()
        url = src.get("url", "").strip()
        if not name or not url:
            logger.warning(
                "Skipping news source at index %d — missing 'name' or 'url'", i
            )
            continue
        sources.append(
            NewsSource(
                name=name,
                url=url,
                category=src.get("category", "general"),
            )
        )

    if not sources:
        raise ValueError("No valid news sources after validation.")

    request = NewsAggregatorRequest(sources=sources, max_per_source=max_articles)

    return NewsAggregatorConfig(request=request, tenant=tenant)
