"""Title Generator — orchestrator (all I/O lives here)."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

from config import load_request
from common.workflows.title_generator import TitleGeneratorService

logger = AppLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"


def save_results(result, request) -> Path:
    """Save results to JSON file in output directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = OUTPUT_DIR / f"{request.channel}_{timestamp}.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "params": {
            "channel": request.channel,
            "niche": request.niche,
            "keyword": request.keyword,
            "style": request.style,
        },
        "results": [
            {"title": o.title, "description": o.description, "reasoning": o.reasoning}
            for o in result.options
        ],
    }
    filepath.write_text(json.dumps(output, indent=2))
    return filepath


def print_results(result, request):
    """Print results in formatted output."""
    print(f"\n{'=' * 70}")
    print(f"Channel: {request.channel} | Niche: {request.niche} | Keyword: {request.keyword}")
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
    service = TitleGeneratorService(
        endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )

    logger.info(f"Generating {request.count} titles for '{request.keyword}' ({request.channel})")

    result = service.generate(
        channel=request.channel,
        niche=request.niche,
        keyword=request.keyword,
        count=request.count,
        style=request.style,
    )

    if result.error:
        logger.error(f"Failed: {result.error}")
        sys.exit(1)

    filepath = save_results(result, request)
    logger.info(f"Saved to: {filepath}")
    print_results(result, request)


if __name__ == "__main__":
    main()
