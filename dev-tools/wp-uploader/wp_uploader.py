"""WP Uploader — orchestrator (all I/O lives here).

Reads topics from CSV, generates LLM content per row,
publishes as draft posts with featured images and keyword tags.

What it does: generate content, set feature image, create draft post.
What still needs manual work: verify content, set category/tags, affiliate links, publish.
"""

import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from shutil import get_terminal_size

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

from config import load_request
from wp_uploader_service import WpUploaderService

logger = AppLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"

# ── Terminal progress helpers ────────────────────────────────────────────────

STEPS = ["LLM Generate", "Publish", "Done"]


def _progress_bar(current: int, total: int, width: int = 30) -> str:
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return f"[{bar}] {current}/{total} ({pct:.0%})"


def _step_indicator(step_idx: int) -> str:
    parts = []
    for i, name in enumerate(STEPS):
        if i < step_idx:
            parts.append(f"  \u2713 {name}")
        elif i == step_idx:
            parts.append(f"  \u25b8 {name}")
        else:
            parts.append(f"  \u00b7 {name}")
    return " ".join(parts)


def _log_header(total: int) -> None:
    cols = get_terminal_size().columns
    logger.info("\u2500" * min(cols, 60))
    logger.info("WP Uploader")
    logger.info(f"Topics: {total} | Output: {OUTPUT_DIR}")
    logger.info("\u2500" * min(cols, 60))


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    data_file = Path(__file__).parent / "data" / "example.json"
    request = load_request(data_file)

    topics_path = Path(__file__).parent / request.topics_file
    if not topics_path.exists():
        logger.error(f"Topics file not found: {topics_path}")
        sys.exit(1)

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
    service = WpUploaderService(wp)

    # Read all rows
    with open(topics_path) as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    if total == 0:
        logger.warning("No topics found in CSV")
        return

    _log_header(total)

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
            niche = row.get("niche", request.niche)
            logger.info("")
            logger.info(f"({i+1}/{total}) {keyword}")
            logger.info(f"  {_progress_bar(i, total)}")
            logger.info(f"  {_step_indicator(0)}")

            try:
                result = service.upload_topic(
                    keyword=keyword,
                    niche=niche,
                    image_url=row.get("image_url", ""),
                    media_id=int(row["media_id"]) if row.get("media_id") else None,
                    status=request.status,
                )

                logger.info(f"  {_step_indicator(2)}")
                logger.info(f"  \u2713 Published: {result.url}")

                writer.writerow([niche, keyword, result.post_id, result.url, result.status])
                completed += 1

            except Exception as e:
                logger.error(f"  \u2717 Failed: {e}")
                failed += 1

    elapsed = time.time() - start_time
    logger.info("")
    logger.info(f"{_progress_bar(total, total)}")
    logger.info("\u2500" * 40)
    logger.info(f"  Completed: {completed}  Failed: {failed}  Elapsed: {elapsed:.1f}s")
    logger.info(f"  Output: {output_file}")
    logger.info("\u2500" * 40)


if __name__ == "__main__":
    main()
