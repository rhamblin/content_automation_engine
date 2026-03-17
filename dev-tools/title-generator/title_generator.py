"""Title Generator — orchestrator (all I/O lives here)."""

import base64
import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from settings import load_dev_settings

from config import load_config
from common.workflows.title_generator import TitleGeneratorService

logger = AppLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"


def save_results(all_results: list[dict], request) -> Path:
    """Save results to JSON file in output directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"{request.channel}_{timestamp}.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "params": {
            "tenant": request.tenant,
            "channel": request.channel,
            "niche": request.niche,
        },
        "results": all_results,
    }
    filepath.write_text(json.dumps(output, indent=2))
    return filepath


def print_results(all_results: list[dict], request):
    """Print results in formatted output."""
    for entry in all_results:
        keyword = entry["keyword"]
        print(f"\n{'=' * 70}")
        print(f"Channel: {request.channel} | Niche: {request.niche} | Keyword: {keyword}")
        print(f"{'=' * 70}")

        for i, opt in enumerate(entry["options"], 1):
            print(f"\n--- Option {i} ---")
            print(f"\nTitle:\n  {opt['title']}")
            print(f"\nDescription:\n  {opt['description']}")
            print(f"\nStrategy:\n  {opt['reasoning']}")
            print()


def _pick_random_image(folder_path: str) -> str | None:
    """Pick a random image from folder and return base64-encoded content."""
    folder = Path(folder_path)
    if not folder.is_dir():
        logger.warning("source_imgs_folder not found: %s", folder_path)
        return None

    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = [f for f in folder.iterdir() if f.suffix.lower() in image_exts]
    if not images:
        logger.warning("No images found in: %s", folder_path)
        return None

    chosen = random.choice(images)
    logger.info("    Picked image: %s", chosen.name)
    return base64.b64encode(chosen.read_bytes()).decode()


def main():
    data_file = Path(__file__).parent / "data" / "input.json"
    config = load_config(data_file)
    request = config.request

    settings = load_dev_settings()
    channel = PinterestChannel(prompt_override=config.channel_prompt)
    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(azure_client)
    service = TitleGeneratorService(llm=llm, channel=channel)

    logger.info(
        "Generating titles for %d keywords (%s)",
        len(config.keywords), request.channel,
    )

    all_results: list[dict] = []
    failed = []
    for kw_dict in config.keywords:
        keyword = kw_dict["term"]
        blog_url = kw_dict.get("blog_url", "")
        logger.info("  → %s", keyword)

        # Load optional reference image from source_imgs_folder
        image_base64 = None
        source_folder = kw_dict.get("source_imgs_folder")
        if source_folder:
            image_base64 = _pick_random_image(source_folder)

        result = service.generate(
            niche=request.niche,
            keyword=keyword,
            persona_prompt=config.persona_prompt,
            audience_prompt=config.audience_prompt,
            image_base64=image_base64,
            blog_url=blog_url,
        )
        if result.error:
            logger.error("Failed for '%s': %s", keyword, result.error)
            failed.append(keyword)
            continue

        all_results.append({
            "keyword": keyword,
            "blog_url": blog_url,
            "options": [
                {"title": o.title, "description": o.description, "alt_text": o.alt_text, "reasoning": o.reasoning}
                for o in result.options
            ],
        })

    if not all_results:
        logger.error("All keywords failed")
        sys.exit(1)

    filepath = save_results(all_results, request)
    logger.info("Saved to: %s", filepath)
    print_results(all_results, request)

    if failed:
        logger.warning("Failed keywords: %s", failed)


if __name__ == "__main__":
    main()
