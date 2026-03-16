"""Pinterest Pin Maker — orchestrator (all I/O lives here)."""

import argparse
import random
import re
import sys
from pathlib import Path

from openai import AzureOpenAI
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.workflows.pin_maker import PinMakerService
from settings import load_dev_settings

from config import load_config, load_styles

logger = AppLogger(__name__)


def extract_keyword(filename: str) -> str:
    """Extract keyword from filename like 'lava_cake1.jpg' -> 'lava cake'."""
    stem = Path(filename).stem
    stem = re.sub(r"\d+$", "", stem)
    return re.sub(r"[_-]", " ", stem).strip().lower()


def main():
    print("Pinterest Pin Maker\n")
    parser = argparse.ArgumentParser(description="Generate Pinterest pins")
    parser.add_argument(
        "data_file", nargs="?", type=Path, help="JSON data file (see data/input.json)"
    )
    parser.add_argument(
        "--list-styles", action="store_true", help="List available styles"
    )
    args = parser.parse_args()

    # Load styles from tenant config
    styles = load_styles()

    # --list-styles: no API call needed
    if args.list_styles:
        for name, style in styles.items():
            print(f"  {name}: {style.description}")
        sys.exit(0)

    if not args.data_file:
        parser.error("a data file is required (e.g. data/input.json)")

    # Layer 2: load + validate request + niche config from JSON data file
    config = load_config(args.data_file)
    request = config.request

    if not config.channel_prompt:
        logger.error(
            f"No pinterest channel prompt configured for niche '{request.niche}'. "
            "Add channel_prompts.pinterest to the niche JSON."
        )
        sys.exit(1)

    # Wire up providers
    settings = load_dev_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    llm = AzureFoundryLLMProvider(client)
    channel = PinterestChannel(prompt_override=config.channel_prompt)

    service = PinMakerService(llm=llm, channel=channel)

    style_names = request.styles or list(styles.keys())

    # ── Keyword-image list mode ──────────────────────────────────────────────
    if request.keywords is not None:
        logger.info(f"Keyword-image mode: {len(request.keywords)} entries")

        # Determine output folder (next to first image, or cwd)
        first_path = Path(request.keywords[0].get("image_path", ""))
        output_folder = (
            first_path.parent / "output"
            if first_path.parent.is_dir()
            else Path("output")
        )
        output_folder.mkdir(exist_ok=True)

        saved, errors = 0, 0
        for idx, entry in enumerate(request.keywords):
            keyword = entry.get("keyword", "")
            image_path = Path(entry.get("image_path", ""))
            if not keyword:
                logger.warning(f"  Skipping entry {idx}: missing keyword")
                errors += 1
                continue
            if not image_path.is_file():
                logger.warning(
                    f"  Skipping '{keyword}': image not found at {image_path}"
                )
                errors += 1
                continue

            style_name = random.choice(style_names)
            style = styles[style_name]
            logger.info(f"  {image_path.name} -> '{keyword}' [{style_name}]")

            try:
                source_image = Image.open(image_path).convert("RGB")
                result = service.make_pin(
                    source_image=source_image,
                    keyword=keyword,
                    niche=request.niche,
                    locale=request.locale,
                    style=style,
                    brand_text=config.brand_watermark,
                    persona_prompt=config.persona_prompt or None,
                    audience_prompt=config.audience_prompt or None,
                )
                out_path = output_folder / f"{image_path.stem}_{result.style_name}.jpg"
                result.image.save(out_path, "JPEG", quality=95)
                logger.info(f"    Saved: {out_path}")
                saved += 1
            except Exception as e:
                logger.error(f"    Error processing '{keyword}': {e}")
                errors += 1

        logger.info(f"Done — {saved} saved, {errors} errors. Output: {output_folder}")
        return

    # ── Folder scan mode ─────────────────────────────────────────────────────
    input_folder = Path(request.input_folder)

    if not input_folder.is_dir():
        logger.error(f"{input_folder} is not a directory")
        sys.exit(1)

    output_folder = input_folder / "output"
    output_folder.mkdir(exist_ok=True)

    # Collect image files
    jpg_files = list(input_folder.glob("*.jpg")) + list(input_folder.glob("*.jpeg"))
    jpg_files += list(input_folder.glob("*.JPG")) + list(input_folder.glob("*.JPEG"))
    logger.info(f"Found {len(jpg_files)} images")

    if len(jpg_files) > len(style_names):
        logger.warning(
            f"{len(jpg_files)} images but only {len(style_names)} styles — some will repeat"
        )

    # Process each image
    saved, errors = 0, 0
    for idx, img_path in enumerate(jpg_files):
        keyword = extract_keyword(img_path.name)
        style_name = random.choice(style_names)
        style = styles[style_name]
        logger.info(f"{img_path.name} -> '{keyword}' [{style_name}]")

        try:
            source_image = Image.open(img_path).convert("RGB")
            result = service.make_pin(
                source_image=source_image,
                keyword=keyword,
                niche=request.niche,
                locale=request.locale,
                style=style,
                brand_text=config.brand_watermark,
                persona_prompt=config.persona_prompt or None,
                audience_prompt=config.audience_prompt or None,
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
