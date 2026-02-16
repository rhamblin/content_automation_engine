"""Title Generator — orchestrator (all I/O lives here)."""

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

from config import load_request
from common.workflows.title_generator import TitleGeneratorService

logger = AppLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"

CHANNELS = {
    "pinterest": lambda: PinterestChannel(),
}


def resolve_channel(name: str):
    """Resolve channel string to IDistributionChannel instance."""
    if name not in CHANNELS:
        raise ValueError(f"Unknown channel '{name}'. Available: {list(CHANNELS.keys())}")
    return CHANNELS[name]()


def save_results(all_results: dict[str, "TitleGenResult"], request) -> Path:
    """Save results to JSON file in output directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"{request.channel}_{timestamp}.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "params": {
            "channel": request.channel,
            "niche": request.niche,
            "keywords": list(request.keywords),
            "style": request.style,
        },
        "results": {
            keyword: [
                {"title": o.title, "description": o.description, "reasoning": o.reasoning}
                for o in result.options
            ]
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
    data_file = Path(__file__).parent / "data" / "example.json"
    request = load_request(data_file)

    settings = load_dev_settings()
    channel = resolve_channel(request.channel)
    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(azure_client)
    service = TitleGeneratorService(llm=llm, channel=channel)

    logger.info(f"Generating {request.count} title(s) each for {len(request.keywords)} keywords ({request.channel})")

    all_results: dict[str, object] = {}
    failed = []
    for keyword in request.keywords:
        logger.info(f"  → {keyword}")
        result = service.generate(
            niche=request.niche,
            keyword=keyword,
            count=request.count,
            copy_style_prompt=request.style,
        )
        if result.error:
            logger.error(f"Failed for '{keyword}': {result.error}")
            failed.append(keyword)
            continue
        all_results[keyword] = result

    if not all_results:
        logger.error("All keywords failed")
        sys.exit(1)

    filepath = save_results(all_results, request)
    logger.info(f"Saved to: {filepath}")
    print_results(all_results, request)

    if failed:
        logger.warning(f"Failed keywords: {failed}")


if __name__ == "__main__":
    main()
