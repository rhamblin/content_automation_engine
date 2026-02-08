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
from common.providers.text.azure_foundry import AzureFoundryTextProvider
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

OUTPUT_DIR = Path(__file__).parent / "output"
TOPICS_FILE = Path(__file__).parent / "input/content_topics.csv"

PROMPT = """
Role:
You are a professional recipe content creator for ChefExotic.com.
Your persona is a warm, friendly home cook (housewife style) who writes in an inviting, comforting, family-oriented tone.

Goal:
Generate a fully formatted, SEO-optimized recipe post for a given keyword (#KEYWORD).
The output must be returned as valid JSON with styled HTML suitable for WordPress visual editors (Elementor or Astra theme).

Output Schema (must always use this format):
{
  "title": "SEO-optimized recipe title",
  "content": "Full styled HTML ready for WordPress visual or Elementor editor"
}

Formatting Rules:
- Wrap all content inside:
  <div class="recipe-content" style="font-family: Arial, sans-serif; color:#333; line-height:1.6; max-width:860px; margin:auto;"> ... </div>
- Use semantic HTML tags: <h2>, <h3>, <p>, <ul>, <ol>, <table>, <a>, <div>
- Inline-style all key elements:
  • Headings: font-size 26 to 28px; margin-top 20 to 24px
  • Paragraphs: font-size 16px
  • Amazon buttons uses this style: style="display: inline-block; background: #ff9900; color: #111; padding: 10px 16px; border-radius: 999px; font-weight: 700 bold; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  • Tables must use <table class="chefexotic-table"> with standard borders and padding
- Include emoji icons to add warmth to headings and list items (e.g., 🍫 🧁 💕)
- Never use Markdown or plaintext formatting.
- Ensure all affiliate links include rel="nofollow noopener sponsored"

Content Structure (must appear in this order):
1. Friendly Introduction 🍫
2. “Jump to Recipe” button
3. One image using the provided URL (if available) with alt text set to the keyword
4. Ingredients list with icons
5. Equipment Needed (with Amazon affiliate "Check price on Amazon" CTAs)
6. Step-by-Step Instructions with icons
7. Health Benefits
8. Nutritional Value Table
9. Serving Suggestions
10. ChefExotic Tips
11. Perfect For (occasions/audiences)
12. Amazon Product Comparison Table
13. Friendly Conclusion

Compliance:
- Include FTC disclosure near all affiliate links:
  <p style="font-size:12px; color:#666;">Disclosure: As an Amazon Associate I earn from qualifying purchases.
  If you click a link and make a purchase, I may receive a commission at no extra cost to you.</p>
- Must be compliant with Google AdSense, Amazon Associates, and ClickBank guidelines.
- Avoid making medical or health claims beyond general benefits.

SEO & Style:
- Integrate keywords naturally.
- Use engaging, family-friendly tone; sound like you are chatting with friends in your kitchen.
- Match tone and structure similar to:
  https://chefexotic.com/main-dishes/baked-pork-tenderloin/

Output:
Return ONLY valid JSON in the exact schema above, containing styled HTML with sectioned formatting for WordPress or Elementor editors.
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
                content = text_provider.generate_text(
                    niche=row["niche"],
                    keyword=row["keyword"],
                    channel=wp,
                    image_url=row["image_url"],
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
