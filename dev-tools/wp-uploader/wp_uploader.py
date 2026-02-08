"""Generate and publish content to WordPress using Azure Foundry."""

import csv
import sys
from datetime import datetime
from pathlib import Path

from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel
from common.providers.text.azure_foundry import AzureFoundryTextProvider
from openai import AzureOpenAI
from settings import load_dev_settings

sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_DIR = Path(__file__).parent / "output"


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
    wp = WordPressChannel(
        settings.wp_site_url, settings.wp_username, settings.wp_app_password
    )

    # Create output CSV for this run
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    with open(TOPICS_FILE) as f, open(output_file, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["niche", "keyword", "post_id", "url", "status"])

        for row in csv.DictReader(f):
            logger.info(f"Processing: {row['niche']} / {row['keyword']}")

            try:
                content = text_provider.generate_text(row["niche"], row["keyword"], wp)
                result = wp.publish(
                    title=content.get("title", "Untitled"),
                    content=content.get("content", ""),
                    media_id=int(row["media_id"]) if row.get("media_id") else None,
                    status="draft",
                )
                logger.info(f"Created: {result['url']}")
                writer.writerow(
                    [
                        row["niche"],
                        row["keyword"],
                        result["post_id"],
                        result["url"],
                        result["status"],
                    ]
                )
            except Exception as e:
                logger.error(f"Failed: {e}")

    logger.info(f"Results written to {output_file}")


if __name__ == "__main__":
    main()
