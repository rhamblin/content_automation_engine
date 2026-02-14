import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

if not Path(".env").exists():
    sys.exit("Error: Run from dev-tools/ directory or use 'make wp-upload'")

load_dotenv(".env")


def _read_secret(path: str) -> str:
    return Path(path).read_text().strip()


@dataclass(frozen=True)
class DevToolSettings:
    """Lightweight settings for dev-tools scripts."""

    azure_foundry_endpoint: str
    azure_foundry_api_key: str
    azure_foundry_api_version: str = "2024-12-01-preview"

    wp_site_url: str = ""
    wp_username: str = ""
    wp_app_password: str = ""

    wp_niche: str = "food"
    wp_amazon_tag: str = ""


def load_dev_settings() -> DevToolSettings:
    return DevToolSettings(
        azure_foundry_endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT", ""),
        azure_foundry_api_key=_read_secret(
            "../secrets/azure-foundry-proj-default-api-key.txt"
        ),
        azure_foundry_api_version=os.getenv(
            "AZURE_FOUNDRY_API_VERSION", "2024-12-01-preview"
        ),
        wp_site_url=os.getenv("WP_SITE_URL", ""),
        wp_username=os.getenv("WP_USERNAME", ""),
        wp_app_password=_read_secret("wp-uploader/wp-app-password.txt"),
        wp_niche=os.getenv("WP_NICHE", "food"),
        wp_amazon_tag=os.getenv("WP_AMAZON_TAG", ""),
    )
