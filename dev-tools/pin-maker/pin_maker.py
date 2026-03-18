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

from config import load_config, load_styles

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

    if not args.data_file and not args.list_styles:
        parser.error("a data file is required (e.g. data/input.json)")

    # Read tenant from data file (default: dev-tenant)
    tenant = "dev-tenant"
    if args.data_file:
        raw = json.loads(args.data_file.read_text())
        tenant = raw.get("tenant", "dev-tenant")

    # Load styles from tenant config
    styles = load_styles(tenant=tenant)

    # --list-styles: no API call needed
    if args.list_styles:
        for name, style in styles.items():
            print(f"  {name}: {style.description}")
        sys.exit(0)

    # Load + validate request + niche config (keywords come from niche config)
    config = load_config(args.data_file, tenant=tenant)
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

    # Create timestamped output folder
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_folder = Path(request.output_folder) / f"{request.niche}-{timestamp}"
    output_folder.mkdir(parents=True, exist_ok=True)

    # Process each active keyword
    manifest = []
    saved, errors = 0, 0

    for kw in config.keywords:
        term = kw["term"]
        blog_url = kw.get("blog_url", "")
        reference_images = kw.get("reference_images", "")

        # Validate reference_images
        if not reference_images:
            logger.error(f"FAILED '{term}': reference_images is not set")
            errors += 1
            continue

        img_dir = Path(reference_images)
        if not img_dir.is_dir():
            logger.error(f"FAILED '{term}': reference_images not found at {img_dir}")
            errors += 1
            continue

        # Collect images from source folder
        images = []
        for ext in IMAGE_EXTENSIONS:
            images.extend(img_dir.glob(ext))
        if not images:
            logger.error(f"FAILED '{term}': no images in {img_dir}")
            errors += 1
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
                product=config.product,
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
        f"Done — {saved} saved, {errors} errors. "
        f"Output: {output_folder}"
    )


if __name__ == "__main__":
    main()
