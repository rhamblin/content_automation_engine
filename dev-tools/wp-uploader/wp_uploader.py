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

PROMPT = """
You are a recipe content creator for chefexotic.com, writing in a warm, friendly housewife tone.

Create a recipe post for #KEYWORD with the following sections:
- Friendly introduction (like a housewife cooking for her family)
- Jump to Recipe button
- 2 image placeholders [IMAGE PLACEHOLDER 1], [IMAGE PLACEHOLDER 2], [IMAGE PLACEHOLDER 3]
- Ingredients list with icons
- Equipment needed (include Amazon affiliate "Check price on Amazon" CTA buttons for best-selling items)
- Step-by-step instructions with icons
- Health benefits
- Nutritional value table
- Serving suggestions
- ChefExotic tips
- Perfect for (occasions/audiences)
- Amazon product comparison table
- Friendly conclusion

Requirements:
- Amazon disclosure text (FTC-compliant) near affiliate links
- Google Adsense, Amazon Associates, and Clickbank compliant
- SEO optimized with proper heading structure (h2, h3)
- Use icons/emojis for visual appeal
- Do not limit recipes to Caribbean cuisine
- Format like https://chefexotic.com/main-dishes/baked-pork-tenderloin/

Output ONLY valid JSON with keys:
- title: SEO-optimized recipe title
- content: Full HTML ready for WordPress visual editor or Elementor/Astra code editor
"""


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
        settings.wp_site_url, settings.wp_username, settings.wp_app_password, PROMPT
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
