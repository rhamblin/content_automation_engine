"""Generate and publish content to WordPress using Azure Foundry.
What it does
--------------
Makes content and put it in place with the image
Set feature image
Sets it as a draft post

What it doesn't do i.e. what still needs to be done manually
------------------
Verifying content / recipe looks good
Putting page as the right category
Setting any tags needed
Modifying any buttons/links so they are pointing to the right affiliate pages
Adding any additional monetization vehicles
Publishing page
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

OUTPUT_DIR = Path(__file__).parent / "output"
TOPICS_FILE = Path(__file__).parent / "input/content_topics.csv"


def main():
    logger = AppLogger(__name__)
    settings = load_dev_settings()

    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(azure_client)
    wp = WordPressChannel(
        site_url=settings.wp_site_url,
        username=settings.wp_username,
        app_password=settings.wp_app_password,
        llm=llm,
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
                content = wp.render_content(
                    source=None,
                    text_data={
                        "niche": row["niche"],
                        "keyword": row["keyword"],
                        "image_url": row["image_url"],
                    },
                )
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
