"""Generate and publish content to WordPress using Azure Foundry.

Reads topics from input/content_topics.csv, generates LLM content per row,
publishes as draft posts with featured images and keyword tags.
Config is pulled from .env (WP_NICHE, WP_AMAZON_TAG, WP_PERSONA).

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
import time
from datetime import datetime
from pathlib import Path
from shutil import get_terminal_size

from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

OUTPUT_DIR = Path(__file__).parent / "output"
TOPICS_FILE = Path(__file__).parent / "input/content_topics.csv"

# ── Terminal progress helpers ────────────────────────────────────────────────

STEPS = ["LLM Generate", "Publish", "Done"]


def _progress_bar(current: int, total: int, width: int = 30) -> str:
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total} ({pct:.0%})"


def _step_indicator(step_idx: int) -> str:
    parts = []
    for i, name in enumerate(STEPS):
        if i < step_idx:
            parts.append(f"  ✓ {name}")
        elif i == step_idx:
            parts.append(f"  ▸ {name}")
        else:
            parts.append(f"  · {name}")
    return " ".join(parts)


def _log_header(logger: AppLogger, total: int) -> None:
    cols = get_terminal_size().columns
    logger.info("─" * min(cols, 60))
    logger.info("WP Uploader")
    logger.info(f"Topics: {total} | Output: {OUTPUT_DIR}")
    logger.info("─" * min(cols, 60))


# ── Main ─────────────────────────────────────────────────────────────────────


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
        amazon_tag=settings.wp_amazon_tag,
    )

    # Read all rows first so we know the total
    with open(TOPICS_FILE) as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    if total == 0:
        logger.warning("No topics found in content_topics.csv")
        return

    _log_header(logger, total)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    completed = 0
    failed = 0
    start_time = time.time()

    with open(output_file, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["niche", "keyword", "post_id", "url", "status"])

        for i, row in enumerate(rows):
            keyword = row["keyword"]
            niche = row.get("niche", settings.wp_niche)
            logger.info("")
            logger.info(f"({i+1}/{total}) {keyword}")
            logger.info(f"  {_progress_bar(i, total)}")

            try:
                # Step 1: LLM Generate
                logger.info(f"  {_step_indicator(0)}")
                content = wp.render_content(
                    source=None,
                    text_data={
                        "niche": niche,
                        "keyword": keyword,
                        "image_url": row.get("image_url", ""),
                    },
                )
                logger.info("  ✓ Content generated")

                # Step 2: Publish with keyword as tag
                logger.info(f"  {_step_indicator(1)}")
                tag_words = keyword.split()
                tags = [keyword] if len(tag_words) > 1 else [keyword]

                result = wp.publish(
                    title=content.get("title", "Untitled"),
                    content=content.get("content", ""),
                    media_id=int(row["media_id"]) if row.get("media_id") else None,
                    status="draft",
                    tags=tags,
                )

                # Step 3: Done
                logger.info(f"  {_step_indicator(2)}")
                logger.info(f"  ✓ Published: {result['url']}")

                writer.writerow(
                    [niche, keyword, result["post_id"], result["url"], result["status"]]
                )
                completed += 1

            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                failed += 1

    elapsed = time.time() - start_time
    logger.info("")
    logger.info(f"{_progress_bar(total, total)}")
    logger.info("─" * 40)
    logger.info(f"  Completed: {completed}  Failed: {failed}  Elapsed: {elapsed:.1f}s")
    logger.info(f"  Output: {output_file}")
    logger.info("─" * 40)


if __name__ == "__main__":
    main()
