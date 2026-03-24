"""Pinterest Pin Maker — orchestrator (all I/O lives here)."""

import argparse
import base64
import hashlib
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
from common.utils.images import collect_images

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.workflows.pin_maker import PinMakerService
from settings import load_dev_settings

from config import load_config, load_styles

logger = AppLogger(__name__)

IMAGE_EXTENSIONS = {"*.jpg", "*.jpeg", "*.png", "*.webp", "*.JPG", "*.JPEG", "*.PNG", "*.WEBP"}


def _load_ingredient_images(kw: dict) -> list[Path]:
    """Load ingredient images for a keyword, returning empty list if unavailable."""
    ingredient_path = kw.get("ingredient_images", "")
    if not ingredient_path:
        return []
    img_dir = Path(ingredient_path)
    if not img_dir.is_dir():
        return []
    return collect_images(str(img_dir))


def _pick_ingredient_image(ingredient_images: list[Path], style) -> Image.Image | None:
    """Pick a random ingredient image if the style requires it, else None."""
    if not getattr(style, "use_ingredient_image", False):
        return None
    if not ingredient_images:
        return None
    chosen = random.choice(ingredient_images)
    return Image.open(chosen).convert("RGB")


def _process_keyword(kw, service, styles, style_names, config, request, output_folder):
    """Process a single keyword: iterate all reference images, run LLM + render for each."""
    term = kw["term"]
    blog_url = kw.get("blog_url", "")
    reference_images = kw.get("reference_images", "")
    ingredient_images = _load_ingredient_images(kw)
    saved, errors = 0, 0
    results = []

    if not reference_images:
        logger.error(f"FAILED '{term}': reference_images is not set")
        return results, 0, 1

    img_dir = Path(reference_images)
    if not img_dir.is_dir():
        logger.error(f"FAILED '{term}': reference_images not found at {img_dir}")
        return results, 0, 1

    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(img_dir.glob(ext))
    if not images:
        logger.error(f"FAILED '{term}': no images in {img_dir}")
        return results, 0, 1

    logger.info(f"'{term}': {len(images)} reference image(s) found")

    for img_path in sorted(images):
        style_name = random.choice(style_names)
        style = styles[style_name]
        logger.info(f"  '{term}' [{style_name}] <- {img_path.name}")

        try:
            source_image = Image.open(img_path).convert("RGB")
            image_b64 = base64.b64encode(img_path.read_bytes()).decode()
            ingredient_img = _pick_ingredient_image(ingredient_images, style)
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
                image_base64=image_b64,
                ingredient_image=ingredient_img,
            )

            slug = term.lower().replace(" ", "_")
            short_hash = hashlib.md5(img_path.name.encode()).hexdigest()[:4]
            out_name = f"{slug}_{short_hash}.jpg"
            out_path = output_folder / out_name
            result.image.save(out_path, "JPEG", quality=95)
            logger.info(f"    Saved: {out_path}")
            saved += 1

            results.append({
                "keyword": term,
                "style_name": result.style_name,
                "output_file": out_name,
                "source_image": str(img_path),
            })

        except Exception as e:
            logger.error(f"    Error processing '{term}' with {img_path.name}: {e}")
            errors += 1

    return results, saved, errors


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

    # Process each active keyword (all images per keyword)
    manifest = []
    saved, errors = 0, 0

    for kw in config.keywords:
        kw_results, kw_saved, kw_errors = _process_keyword(
            kw, service, styles, style_names, config, request, output_folder
        )
        manifest.extend(kw_results)
        saved += kw_saved
        errors += kw_errors

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
