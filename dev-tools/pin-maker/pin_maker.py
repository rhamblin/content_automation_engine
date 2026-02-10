"""Pinterest Pin Maker - Generate pins with LLM text and style selection."""

import argparse
import json
import re
import sys
from pathlib import Path

from openai import AzureOpenAI
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings
from styles import BRAND_TEXT, STYLES, get_style_brief

# Pinterest dimensions (2:3)
PIN_WIDTH = 1000
PIN_HEIGHT = 1500

PROMPT = f"""
You are a Pinterest marketing expert creating eye-catching pin text for food/recipe images.

Given a keyword, generate compelling pin text AND select the best visual style.

{get_style_brief()}

Output Schema:
{{
  "style": "style_name from list above",
  "title": "Catchy title (2-4 words, ALL CAPS)",
  "tagline": "Benefit tagline (2-4 words, ALL CAPS, periods between words)",
  "time_text": "Time indicator (e.g., 'In 30 MINUTES')",
  "prefix": "Optional prefix like '30-Minute' or null",
  "accent": "Optional elegant phrase like 'with Parmesan' or null"
}}

Guidelines:
- Match style to the dish mood
- Title should be punchy and appetizing
- Include the main keyword naturally in the title
- Tagline should highlight ease, occasion, or benefit
- Time should be realistic for the dish type
- Use prefix for time-based or descriptor prefixes (e.g., "Quick & Easy", "30-Minute")
- Use accent for elegant sub-phrases (e.g., "with Parmesan", "with Ricotta Cheese")

Return ONLY valid JSON.
"""


def smart_crop_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize and crop image to target dimensions, preserving center content."""
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


def extract_keyword(filename: str) -> str:
    """Extract keyword from filename like 'lava_cake1.jpg' -> 'lava cake'."""
    stem = Path(filename).stem
    stem = re.sub(r"\d+$", "", stem)
    return re.sub(r"[_-]", " ", stem).strip().lower()


def generate_pin_data(client: AzureOpenAI, keyword: str, model: str) -> dict:
    """Generate pin text and style selection via LLM."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"Keyword: {keyword}"},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def create_pin(img_path: Path, pin_data: dict, style_name: str, output_path: Path) -> None:
    """Create a Pinterest pin with text overlay using specified style."""
    style = STYLES.get(style_name)
    if not style:
        print(f"  Warning: Style '{style_name}' not found, using 'bold_rustic'")
        style = STYLES["bold_rustic"]

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
    parser.add_argument("--style", type=str, help="Force a specific style (skip LLM selection)")
    parser.add_argument("--list-styles", action="store_true", help="List available styles")
    args = parser.parse_args()

    if args.list_styles:
        print("Available styles:")
        for name, style in STYLES.items():
            print(f"  {name}: {style.description}")
        sys.exit(0)

    if not args.folder.is_dir():
        print(f"Error: {args.folder} is not a directory")
        sys.exit(1)

    output_folder = args.folder / "output"
    output_folder.mkdir(exist_ok=True)

    settings = load_dev_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )

    jpg_files = list(args.folder.glob("*.jpg")) + list(args.folder.glob("*.JPG"))
    jpg_files += list(args.folder.glob("*.jpeg")) + list(args.folder.glob("*.JPEG"))

    if not jpg_files:
        print(f"No JPG files found in {args.folder}")
        sys.exit(1)

    print(f"Found {len(jpg_files)} images to process")

    for img_path in jpg_files:
        keyword = extract_keyword(img_path.name)
        print(f"\nProcessing: {img_path.name} -> '{keyword}'")

        try:
            pin_data = generate_pin_data(client, keyword, settings.azure_foundry_model)

            style_name = args.style or pin_data.get("style", "bold_rustic")

            print(f"  Style: {style_name}")
            print(f"  Title: {pin_data.get('title', 'N/A')}")
            if pin_data.get("prefix"):
                print(f"  Prefix: {pin_data['prefix']}")
            if pin_data.get("accent"):
                print(f"  Accent: {pin_data['accent']}")
            if pin_data.get("tagline"):
                print(f"  Tagline: {pin_data['tagline']}")
            if pin_data.get("time_text"):
                print(f"  Time: {pin_data['time_text']}")

            output_path = output_folder / f"pin_{img_path.stem}.jpg"
            create_pin(img_path, pin_data, style_name, output_path)
            print(f"  Saved: {output_path}")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"\nDone! Pins saved to {output_folder}")


if __name__ == "__main__":
    main()
