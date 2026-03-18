"""Pinterest Pin Maker — orchestrator (all I/O lives here)."""

import argparse
import json
import random
import sys
from datetime import datetime
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

from config import _to_slug, load_config, load_styles

logger = AppLogger(__name__)

IMAGE_EXTENSIONS = {"*.jpg", "*.jpeg", "*.png", "*.webp", "*.JPG", "*.JPEG", "*.PNG", "*.WEBP"}


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

    # Load + validate request + niche config (keywords come from niche config)
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

    # Resolve input folder and create timestamped output folder as sibling
    input_folder = Path(request.input_folder)
    if not input_folder.is_dir():
        logger.error(f"{input_folder} is not a directory")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_folder = input_folder.parent / f"output-{timestamp}"
    output_folder.mkdir(parents=True, exist_ok=True)

    # Process each active keyword
    manifest = []
    saved, errors, skipped = 0, 0, 0
    seen_slugs = set()

    for kw in config.keywords:
        term = kw["term"]
        blog_url = kw.get("blog_url", "")
        slug = _to_slug(term)

        # Warn on duplicate slugs
        if slug in seen_slugs:
            logger.warning(f"Duplicate slug '{slug}' from term '{term}' — processing anyway")
        seen_slugs.add(slug)

        subfolder = input_folder / slug
        if not subfolder.is_dir():
            logger.warning(f"Skipping '{term}': no subfolder at {subfolder}")
            skipped += 1
            continue

        # Collect images from subfolder
        images = []
        for ext in IMAGE_EXTENSIONS:
            images.extend(subfolder.glob(ext))
        if not images:
            logger.warning(f"Skipping '{term}': subfolder {subfolder} has no images")
            skipped += 1
            continue

        # Pick random image and style
        img_path = random.choice(images)
        style_name = random.choice(style_names)
        style = styles[style_name]
        logger.info(f"'{term}' [{style_name}] <- {img_path.name}")

        try:
            source_image = Image.open(img_path).convert("RGB")
            result = service.make_pin(
                source_image=source_image,
                keyword=term,
                niche=request.niche,
                locale=request.locale,
                style=style,
                brand_text=config.brand_watermark,
                persona_prompt=config.persona_prompt or None,
                audience_prompt=config.audience_prompt or None,
                blog_url=blog_url,
            )

            out_name = f"{img_path.stem}_{result.style_name}.jpg"
            out_path = output_folder / out_name
            result.image.save(out_path, "JPEG", quality=95)
            logger.info(f"  Saved: {out_path}")
            saved += 1

            manifest.append({
                "keyword": term,
                "style_name": result.style_name,
                "output_file": out_name,
                "source_image": str(img_path),
            })

        except Exception as e:
            logger.error(f"  Error processing '{term}': {e}")
            errors += 1

    # Write manifest
    manifest_path = output_folder / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Manifest written: {manifest_path}")

    logger.info(
        f"Done — {saved} saved, {errors} errors, {skipped} skipped. "
        f"Output: {output_folder}"
    )


if __name__ == "__main__":
    main()
