"""Config loader — reads JSON data file, resolves niche config."""

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"


@dataclass(frozen=True)
class AccountAnalyticsConfig:
    """Validated config from data file + tenant niche config."""

    tenant: str
    niche: str
    brand_name: str
    brand_website: str


def load_config(path: Path) -> AccountAnalyticsConfig:
    """Load a JSON data file, resolve niche config, return validated config."""
    raw = json.loads(path.read_text())
    tenant = raw.get("tenant", "dev-tenant")
    niche_name = raw.get("niche", "recipes")

    niche_dir = CONFIG_ROOT / tenant / "niches" / niche_name
    niche_json = niche_dir / f"{niche_name}.json"
    if not niche_json.exists():
        raise ValueError(f"niche config not found: {niche_json}")

    niche_data = json.loads(niche_json.read_text())

    return AccountAnalyticsConfig(
        tenant=tenant,
        niche=niche_name,
        brand_name=niche_data.get("brand_name", ""),
        brand_website=niche_data.get("brand_website", ""),
    )
