import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).parent / ".env"

if not _ENV_FILE.exists():
    sys.exit("Error: Run from dev-tools/ directory or use 'make wp-upload'")

load_dotenv(_ENV_FILE)

NICHES_DIR = Path(__file__).parent.parent / "config" / "tenants" / "dev-tenant" / "niches"


def _read_secret(path: str) -> str:
    p = Path(path)
    if p.exists():
        return p.read_text().strip()
    return ""


@dataclass(frozen=True)
class WpNicheCredential:
    """WordPress credentials for a single niche."""
    site_url: str
    username: str
    app_password: str
    amazon_tag: str = ""


@dataclass(frozen=True)
class DevToolSettings:
    """Lightweight settings for dev-tools scripts."""

    azure_foundry_endpoint: str
    azure_foundry_api_key: str
    azure_foundry_api_version: str = "2024-12-01-preview"

    wp_niche: str = "food"
    wp_credentials: dict[str, WpNicheCredential] = field(default_factory=dict)


def _load_wp_niche_credentials() -> dict[str, WpNicheCredential]:
    """Scan niches/<name>/credentials/wordpress.json + secret files."""
    creds: dict[str, WpNicheCredential] = {}
    if not NICHES_DIR.exists():
        return creds

    for niche_dir in sorted(NICHES_DIR.iterdir()):
        if not niche_dir.is_dir():
            continue
        wp_json = niche_dir / "credentials" / "wordpress.json"
        if not wp_json.exists():
            continue

        data = json.loads(wp_json.read_text())
        # Look for app password in a secret file next to the JSON
        secret_file = niche_dir / "credentials" / "wp-app-password.txt"
        app_password = _read_secret(str(secret_file))
        if not app_password:
            app_password = data.get("app_password", "")

        # Look for amazon tag in the niche's JSON config
        niche_json = niche_dir / f"{niche_dir.name}.json"
        amazon_tag = ""
        if niche_json.exists():
            niche_data = json.loads(niche_json.read_text())
            amazon_tag = niche_data.get("amazon_tag", "")

        creds[niche_dir.name] = WpNicheCredential(
            site_url=data.get("site_url", ""),
            username=data.get("username", ""),
            app_password=app_password,
            amazon_tag=amazon_tag,
        )

    return creds


def load_dev_settings() -> DevToolSettings:
    return DevToolSettings(
        azure_foundry_endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT", ""),
        azure_foundry_api_key=_read_secret(
            str(_ENV_FILE.parent / "../secrets/azure-foundry-proj-default-api-key.txt")
        ),
        azure_foundry_api_version=os.getenv(
            "AZURE_FOUNDRY_API_VERSION", "2024-12-01-preview"
        ),
        wp_niche=os.getenv("WP_NICHE", "food"),
        wp_credentials=_load_wp_niche_credentials(),
    )
