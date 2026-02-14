"""Pinterest Pin Maker - Generate pins with LLM text and style selection."""

import argparse
import re
import sys
from pathlib import Path

from openai import AzureOpenAI
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.providers.distribution_channel.pinterest import PinterestChannel
from common.providers.llm.azure_foundry import AzureFoundryLLMProvider

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings
from common.resources.personas import get_persona
from common.providers.distribution_channel.pinterest import STYLES, list_styles


def extract_keyword(filename: str) -> str:
    """Extract keyword from filename like 'lava_cake1.jpg' -> 'lava cake'."""
    stem = Path(filename).stem
    stem = re.sub(r"\d+$", "", stem)
    return re.sub(r"[_-]", " ", stem).strip().lower()


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest pins")
    parser.add_argument("folder", type=Path, help="Folder containing images")
    parser.add_argument("--niche", type=str, default="food", help="Content niche (default: food)")
    parser.add_argument("--locale", type=str, default="en", choices=["en", "es", "sw"], help="Output language (default: en)")
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
    llm = AzureFoundryLLMProvider(client)
    channel = PinterestChannel()
    persona = get_persona(args.niche)

    # Process images
    jpg_files = list(args.folder.glob("*.jpg")) + list(args.folder.glob("*.jpeg"))
    jpg_files += list(args.folder.glob("*.JPG")) + list(args.folder.glob("*.JPEG"))

    print(f"Found {len(jpg_files)} images")

    # Get all style names - each used exactly once
    style_names = list_styles()
    if len(jpg_files) > len(style_names):
        print(f"Warning: {len(jpg_files)} images but only {len(style_names)} styles. Some styles will repeat.")

    for idx, img_path in enumerate(jpg_files):
        keyword = extract_keyword(img_path.name)
        print(f"\n{img_path.name} -> '{keyword}'")

        try:
            # Select style first (use forced style or cycle through styles)
            if args.style:
                style_name = args.style
            else:
                style_name = style_names[idx % len(style_names)]
            style = STYLES[style_name]

            # Generate content - LLM provider combines: channel + persona + style + locale
            text_data = llm.generate(
                niche=args.niche, keyword=keyword, channel=channel, persona=persona, style=style, locale=args.locale
            )

            print(f"  Style: {style_name} | Title: {text_data.get('title')}")

            # Read image
            source_image = Image.open(img_path).convert("RGB")

            # Render content via channel
            pin_image = channel.render_content(
                source=source_image,
                text_data=text_data,
                style=style,
                brand_text=settings.brand_text,
            )

            # Save with style name appended
            output_path = output_folder / f"{img_path.stem}_{style_name}.jpg"
            pin_image.save(output_path, "JPEG", quality=95)
            print(f"  Saved: {output_path}")

        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nDone! Output: {output_folder}")


if __name__ == "__main__":
    main()
