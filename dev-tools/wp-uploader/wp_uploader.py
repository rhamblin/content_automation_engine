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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

from config import load_config
from rich.console import Console
from rich.progress import Progress

from common.workflows.wp_uploader import WpUploaderService

logger = AppLogger(__name__)
console = Console()

OUTPUT_DIR = Path(__file__).parent / "output"


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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    console.rule("[bold]WP Uploader[/bold]")
    console.print(f"Keywords: {total} | Output: {OUTPUT_DIR}")
    console.rule()

    completed = 0
    failed = 0
    skipped = 0
    start_time = time.time()

    with open(output_file, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["niche", "keyword", "post_id", "url", "status"])

        with Progress(console=console) as progress:
            task = progress.add_task("Uploading keywords…", total=total)

            for i, keyword in enumerate(request.keywords):
                progress.update(task, description=f"[cyan]({i+1}/{total})[/cyan] {keyword}")

                # Resolve media from WP library
                media_id, image_url = service.resolve_media(
                    keyword=keyword,
                    site_url=wp_cred.site_url,
                    username=wp_cred.username,
                    app_password=wp_cred.app_password,
                )

                if media_id is None:
                    logger.warning(f"No media found for '{keyword}', skipping")
                    skipped += 1
                    progress.advance(task)
                    continue

                logger.info(f"Media: id={media_id}")

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

                    console.print(f"  [green]✓[/green] Published: {result.url}")
                    writer.writerow([request.niche, keyword, result.post_id, result.url, result.status])
                    completed += 1

                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed: {e}")
                    failed += 1

                progress.advance(task)

    elapsed = time.time() - start_time
    console.rule()
    console.print(f"  Completed: {completed}  Skipped: {skipped}  Failed: {failed}  Elapsed: {elapsed:.1f}s")
    console.print(f"  Output: {output_file}")
    console.rule()


if __name__ == "__main__":
    main()
