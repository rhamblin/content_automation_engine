"""Generate and publish content to WordPress using Azure Foundry."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AzureOpenAI
from settings import load_dev_settings

from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel
from common.providers.text.azure_foundry import AzureFoundryTextProvider

TOPICS_FILE = Path(__file__).parent / "content_topics.csv"


def main():
    logger = AppLogger(__name__)
    settings = load_dev_settings()

    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    text_provider = AzureFoundryTextProvider(azure_client)
    wp = WordPressChannel(settings.wp_site_url, settings.wp_username, settings.wp_app_password)

    with open(TOPICS_FILE) as f:
        for row in csv.DictReader(f):
            logger.info(f"Processing: {row['niche']} / {row['keyword']}")

            try:
                content = text_provider.generate_text(row["niche"], row["keyword"], wp)
                result = wp.publish(
                    title=content.get("title", "Untitled"),
                    description=content.get("content", ""),
                    image_url=row.get("image_uri", ""),
                    excerpt=content.get("excerpt", ""),
                    featured_media=int(row["media_id"]) if row.get("media_id") else None,
                    status="draft",
                )
                logger.info(f"Created: {result['url']}")
            except Exception as e:
                logger.error(f"Failed: {e}")


if __name__ == "__main__":
    main()
