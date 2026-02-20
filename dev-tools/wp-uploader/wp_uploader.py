"""WP Uploader — orchestrator (all I/O lives here).

Reads keywords from data/input.json, resolves media from WP library,
generates LLM content per keyword, publishes as draft posts with featured images and keyword tags.

What it does: resolve media, generate content, set feature image, create draft post.
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

from config import load_config
from common.workflows.wp_uploader import WpUploaderService

logger = AppLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"

# ── Terminal progress helpers ────────────────────────────────────────────────

STEPS = ["Resolve Media", "LLM Generate", "Publish", "Done"]


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
    logger.info(f"Keywords: {total} | Output: {OUTPUT_DIR}")
    logger.info("\u2500" * min(cols, 60))


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    data_file = Path(__file__).parent / "data" / "input.json"
    config = load_config(data_file)
    request = config.request
    prompts = config.niche_prompts

    if not prompts.channel_prompt:
        logger.error(f"No wordpress channel prompt configured for niche '{request.niche}'. "
                      "Add channel_prompts.wordpress to the niche JSON.")
        sys.exit(1)

    settings = load_dev_settings()

    wp_cred = settings.wp_credentials.get(request.niche)
    if not wp_cred:
        logger.error(f"No WordPress credentials for niche '{request.niche}'. "
                      "Add credentials under config/tenants/dev-tenant/niches/<name>/credentials/wordpress.json")
        sys.exit(1)

    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(azure_client)

    wp_channel = WordPressChannel(
        site_url=wp_cred.site_url,
        username=wp_cred.username,
        app_password=wp_cred.app_password,
        llm=llm,
        amazon_tag=wp_cred.amazon_tag,
        prompt_override=prompts.channel_prompt,
    )

    service = WpUploaderService(wp_channel)

    total = len(request.keywords)
    if total == 0:
        logger.warning("No keywords found")
        return

    _log_header(total)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    completed = 0
    failed = 0
    skipped = 0
    start_time = time.time()

    with open(output_file, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["niche", "keyword", "post_id", "url", "status"])

        for i, keyword in enumerate(request.keywords):
            logger.info("")
            logger.info(f"({i+1}/{total}) {keyword}")
            logger.info(f"  {_progress_bar(i, total)}")
            logger.info(f"  {_step_indicator(0)}")

            # Resolve media from WP library
            media_id, image_url = service.resolve_media(
                keyword=keyword,
                site_url=wp_cred.site_url,
                username=wp_cred.username,
                app_password=wp_cred.app_password,
            )

            if media_id is None:
                logger.warning(f"  No media found for '{keyword}', skipping")
                skipped += 1
                continue

            logger.info(f"  {_step_indicator(1)}")
            logger.info(f"  Media: id={media_id}")

            try:
                result = service.upload_topic(
                    keyword=keyword,
                    niche=request.niche,
                    image_url=image_url,
                    media_id=media_id,
                    status=request.status,
                    persona_prompt=prompts.persona_prompt or None,
                    copy_style_prompt=prompts.copy_style_prompt or None,
                    audience_prompt=prompts.audience_prompt or None,
                )

                logger.info(f"  {_step_indicator(3)}")
                logger.info(f"  \u2713 Published: {result.url}")

                writer.writerow([request.niche, keyword, result.post_id, result.url, result.status])
                completed += 1

            except Exception as e:
                logger.error(f"  \u2717 Failed: {e}")
                failed += 1

    elapsed = time.time() - start_time
    logger.info("")
    logger.info(f"{_progress_bar(total, total)}")
    logger.info("\u2500" * 40)
    logger.info(f"  Completed: {completed}  Skipped: {skipped}  Failed: {failed}  Elapsed: {elapsed:.1f}s")
    logger.info(f"  Output: {output_file}")
    logger.info("\u2500" * 40)


if __name__ == "__main__":
    main()
