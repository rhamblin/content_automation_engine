"""Pinterest Pin Maker - Generate pins with LLM text and style selection."""

import argparse
import re
import sys
from pathlib import Path

from openai import AzureOpenAI
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.providers.text.azure_foundry import AzureFoundryTextProvider

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings
from styles import BRAND_TEXT, STYLES, get_style_brief

PIN_WIDTH = 1000
PIN_HEIGHT = 1500


def extract_keyword(filename: str) -> str:
    """Extract keyword from filename like 'lava_cake1.jpg' -> 'lava cake'."""
    stem = Path(filename).stem
    stem = re.sub(r"\d+$", "", stem)
    return re.sub(r"[_-]", " ", stem).strip().lower()


def smart_crop_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize and crop image to target dimensions."""
    orig_w, orig_h = img.size
    target_ratio = target_w / target_h
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
    else:
        new_h = int(orig_w / target_ratio)
        top = (orig_h - new_h) // 3
        img = img.crop((0, top, orig_w, top + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def make_pin(img_path: Path, pin_data: dict, output_path: Path) -> None:
    """Read image, apply style, save output."""
    style_name = pin_data.get("style", "bold_rustic")
    style = STYLES.get(style_name, STYLES["bold_rustic"])

    img = Image.open(img_path).convert("RGB")
    img = smart_crop_resize(img, PIN_WIDTH, PIN_HEIGHT)

    if style.overlay:
        img = style.overlay.apply(img)

    draw = ImageDraw.Draw(img)
    for key, element in style.elements():
        text = BRAND_TEXT if key == "watermark" else pin_data.get(key)
        if text:
            element.draw(draw, text, img.width, img.height)

    img.save(output_path, "JPEG", quality=95)


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest pins")
    parser.add_argument("folder", type=Path, help="Folder containing images")
    parser.add_argument("--style", type=str, help="Force a specific style")
    parser.add_argument("--list-styles", action="store_true", help="List available styles")
    args = parser.parse_args()

    if args.list_styles:
        for name, style in STYLES.items():
            print(f"  {name}: {style.description}")
        sys.exit(0)

    if not args.folder.is_dir():
        print(f"Error: {args.folder} is not a directory")
        sys.exit(1)

    output_folder = args.folder / "output"
    output_folder.mkdir(exist_ok=True)

    # Setup
    settings = load_dev_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    text_provider = AzureFoundryTextProvider(client)
    channel = PinterestChannel(PinterestChannel.build_pin_maker_prompt(get_style_brief()))

    # Process images
    jpg_files = list(args.folder.glob("*.jpg")) + list(args.folder.glob("*.jpeg"))
    jpg_files += list(args.folder.glob("*.JPG")) + list(args.folder.glob("*.JPEG"))

    print(f"Found {len(jpg_files)} images")

    for img_path in jpg_files:
        keyword = extract_keyword(img_path.name)
        print(f"\n{img_path.name} -> '{keyword}'")

        try:
            # Get text from provider
            pin_data = text_provider.generate_text(
                niche="food", keyword=keyword, channel=channel, image_url=""
            )
            if args.style:
                pin_data["style"] = args.style

            print(f"  Style: {pin_data.get('style')} | Title: {pin_data.get('title')}")

            # Make pin and save
            output_path = output_folder / f"pin_{img_path.stem}.jpg"
            make_pin(img_path, pin_data, output_path)
            print(f"  Saved: {output_path}")

        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nDone! Output: {output_folder}")


if __name__ == "__main__":
    main()
