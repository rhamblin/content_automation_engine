"""Title Generator — orchestrator (all I/O lives here)."""

import base64
import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.utils.images import collect_images
from common.utils.string_utils import to_camel_case
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
        source_image = entry.get("source_image", "")
        print(f"\n{'=' * 70}")
        header = f"Channel: {request.channel} | Niche: {request.niche} | Keyword: {keyword}"
        if source_image:
            header += f" | Image: {source_image}"
        print(header)
        print(f"{'=' * 70}")

        for i, opt in enumerate(entry["options"], 1):
            print(f"\n--- Option {i} ---")
            print(f"\nTitle:\n  {opt['title']}")
            print(f"\nDescription:\n  {opt['description']}")
            print(f"\nStrategy:\n  {opt['reasoning']}")
            print()


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
    keywords = list(config.keywords)
    random.shuffle(keywords)
    for kw_dict in keywords:
        keyword = kw_dict["term"]
        blog_url = kw_dict.get("blog_url", "")
        source_folder = kw_dict.get("reference_images")

        # Build list of (image_base64, source_image_name) to iterate
        image_items: list[tuple[str | None, str]] = []
        if source_folder:
            images = collect_images(source_folder)
            if not images:
                logger.warning("No images for '%s', skipping", keyword)
                failed.append(keyword)
                continue
            random.shuffle(images)
            for img_path in images:
                b64 = base64.b64encode(img_path.read_bytes()).decode()
                image_items.append((b64, img_path.name))
        else:
            # No reference_images — run once with no image
            image_items.append((None, ""))

        logger.info("  → %s (%d image(s))", keyword, len(image_items))

        for image_base64, source_image in image_items:
            if source_image:
                logger.info("    ← %s", source_image)

            result = service.generate(
                niche=request.niche,
                keyword=keyword,
                persona_prompt=config.persona_prompt,
                audience_prompt=config.audience_prompt,
                image_base64=image_base64,
                blog_url=blog_url,
            )
            if result.error:
                logger.error("Failed for '%s' [%s]: %s", keyword, source_image, result.error)
                failed.append(keyword)
                continue

            tags = [to_camel_case(t) for t in [config.niche_title, keyword]]
            hashtags = " ".join(f"#{t}" for t in tags)

            all_results.append({
                "keyword": keyword,
                "blog_url": blog_url,
                "source_image": source_image,
                "options": [
                    {
                        "title": o.title,
                        "description": f"{o.description}\n\n{hashtags}",
                        "alt_text": o.alt_text,
                        "reasoning": o.reasoning,
                    }
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
