"""Pinterest Pin Maker — orchestrator (all I/O lives here)."""

import argparse
import re
import sys
from pathlib import Path

from openai import AzureOpenAI
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.providers.distribution_channel.pinterest import PinterestChannel, list_styles
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider
from common.resources.personas import get_persona

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

from pin_maker_service import PinMakerService

logger = AppLogger(__name__)


def extract_keyword(filename: str) -> str:
    """Extract keyword from filename like 'lava_cake1.jpg' -> 'lava cake'."""
    stem = Path(filename).stem
    stem = re.sub(r"\d+$", "", stem)
    return re.sub(r"[_-]", " ", stem).strip().lower()


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest pins")
    parser.add_argument("data_file", nargs="?", type=Path, help="JSON data file (see data/example.json)")
    parser.add_argument("--list-styles", action="store_true", help="List available styles")
    args = parser.parse_args()

    # --list-styles: no API call needed
    if args.list_styles:
        for name, desc in PinMakerService.list_styles().items():
            print(f"  {name}: {desc}")
        sys.exit(0)

    if not args.data_file:
        parser.error("a data file is required (e.g. data/example.json)")

    # Layer 2: load + validate request from JSON data file
    from config import load_request

    request = load_request(args.data_file)
    input_folder = Path(request.input_folder)

    if not input_folder.is_dir():
        logger.error(f"{input_folder} is not a directory")
        sys.exit(1)

    output_folder = input_folder / "output"
    output_folder.mkdir(exist_ok=True)

    # Wire up providers
    settings = load_dev_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(client)
    channel = PinterestChannel()
    persona = get_persona(request.niche)

    service = PinMakerService(llm=llm, channel=channel, persona=persona)

    # Collect image files
    jpg_files = list(input_folder.glob("*.jpg")) + list(input_folder.glob("*.jpeg"))
    jpg_files += list(input_folder.glob("*.JPG")) + list(input_folder.glob("*.JPEG"))
    logger.info(f"Found {len(jpg_files)} images")

    style_names = list_styles()
    if len(jpg_files) > len(style_names):
        logger.warning(f"{len(jpg_files)} images but only {len(style_names)} styles — some will repeat")

    # Process each image
    saved, errors = 0, 0
    for idx, img_path in enumerate(jpg_files):
        keyword = extract_keyword(img_path.name)
        style_name = request.style or style_names[idx % len(style_names)]
        logger.info(f"{img_path.name} -> '{keyword}' [{style_name}]")

        try:
            source_image = Image.open(img_path).convert("RGB")
            result = service.make_pin(
                source_image=source_image,
                keyword=keyword,
                niche=request.niche,
                locale=request.locale,
                style_name=style_name,
                brand_text=settings.brand_text,
            )

            output_path = output_folder / f"{img_path.stem}_{result.style_name}.jpg"
            result.image.save(output_path, "JPEG", quality=95)
            logger.info(f"  Saved: {output_path}")
            saved += 1

        except Exception as e:
            logger.error(f"  Error processing {img_path.name}: {e}")
            errors += 1

    logger.info(f"Done — {saved} saved, {errors} errors. Output: {output_folder}")


if __name__ == "__main__":
    main()
