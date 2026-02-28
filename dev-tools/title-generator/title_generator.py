"""Title Generator — orchestrator (all I/O lives here)."""

import base64
import json
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


def save_results(all_results: dict[str, "TitleGenResult"], request, keyword_blog_urls: dict[str, str]) -> Path:
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
            "keywords": list(request.keywords),
        },
        "results": {
            keyword: {
                "blog_url": keyword_blog_urls.get(keyword, ""),
                "options": [
                    {"title": o.title, "description": o.description, "alt_text": o.alt_text, "reasoning": o.reasoning}
                    for o in result.options
                ],
            }
            for keyword, result in all_results.items()
        },
    }
    filepath.write_text(json.dumps(output, indent=2))
    return filepath


def print_results(all_results: dict[str, "TitleGenResult"], request):
    """Print results in formatted output."""
    for keyword, result in all_results.items():
        print(f"\n{'=' * 70}")
        print(f"Channel: {request.channel} | Niche: {request.niche} | Keyword: {keyword}")
        print(f"{'=' * 70}")

        for i, opt in enumerate(result.options, 1):
            print(f"\n--- Option {i} ---")
            print(f"\nTitle:\n  {opt.title}")
            print(f"\nDescription:\n  {opt.description}")
            print(f"\nStrategy:\n  {opt.reasoning}")
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

    logger.info(f"Generating {request.count} title(s) each for {len(request.keywords)} keywords ({request.channel})")

    data_dir = Path(__file__).parent

    all_results: dict[str, object] = {}
    failed = []
    for keyword in request.keywords:
        logger.info(f"  → {keyword}")

        # Load optional reference image for grounding
        image_base64 = None
        image_path = config.keyword_images.get(keyword)
        if image_path:
            abs_path = data_dir / image_path
            if abs_path.is_file():
                image_base64 = base64.b64encode(abs_path.read_bytes()).decode()
                logger.info(f"    Attached image: {image_path}")
            else:
                raise FileNotFoundError(f"Image not found: {abs_path}")

        blog_url = config.keyword_blog_urls.get(keyword, "")

        result = service.generate(
            niche=request.niche,
            keyword=keyword,
            count=request.count,
            persona_prompt=config.persona_prompt,
            audience_prompt=config.audience_prompt,
            image_base64=image_base64,
            blog_url=blog_url,
        )
        if result.error:
            logger.error(f"Failed for '{keyword}': {result.error}")
            failed.append(keyword)
            continue
        all_results[keyword] = result

    if not all_results:
        logger.error("All keywords failed")
        sys.exit(1)

    filepath = save_results(all_results, request, config.keyword_blog_urls)
    logger.info(f"Saved to: {filepath}")
    print_results(all_results, request)

    if failed:
        logger.warning(f"Failed keywords: {failed}")


if __name__ == "__main__":
    main()
