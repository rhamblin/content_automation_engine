"""Pinterest Pin Maker - Generate Pinterest-worthy pins from images.

Takes a folder of JPG images, extracts keywords from filenames,
generates catchy text via Azure Foundry, and creates pin images
with text overlays using PIL.
"""

import re
import sys
from pathlib import Path

from openai import AzureOpenAI
from PIL import Image, ImageDraw, ImageFont

from common.contracts.interfaces import IDistributionChannel
from common.providers.text.azure_foundry import AzureFoundryTextProvider

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

# Pinterest optimal dimensions (2:3 ratio)
PIN_WIDTH = 1000
PIN_HEIGHT = 1500

PROMPT = """
You are a Pinterest marketing expert creating eye-catching pin text for food/recipe images.

Given a keyword, generate compelling pin text that will drive clicks and saves.

Output Schema (must always use this format):
{
  "title": "Catchy, bold title (2-4 words max, ALL CAPS, include an adjective)",
  "tagline": "Short benefit tagline (2-4 words, ALL CAPS, use periods between words like EASY. WEEKNIGHT. DINNER.)",
  "time_text": "Time indicator (e.g., 'In 30 MINUTES', 'Ready in 15 MIN', 'Under 1 HOUR')"
}

Guidelines:
- Title should be punchy and appetizing (e.g., "JUICY BAKED PORK", "CRISPY FRIED CHICKEN")
- Include the main keyword naturally in the title
- Tagline should highlight ease, occasion, or benefit
- Time should be realistic for the dish type
- Make it scroll-stopping and clickable

Return ONLY valid JSON.
"""


class PinterestChannel(IDistributionChannel):
    """Minimal channel implementation for Pinterest pin text generation."""

    PROVIDER_NAME = "pinterest"

    def __init__(self, prompt: str):
        self._prompt = prompt

    @property
    def system_prompt(self) -> str:
        return self._prompt

    def publish(self, title: str, content: str, image_url: str, **kwargs) -> dict:
        raise NotImplementedError("Pinterest pins are saved locally, not published")


def extract_keyword(filename: str) -> str:
    """Extract keyword from filename like 'lava_cake1.jpg' -> 'lava cake'."""
    stem = Path(filename).stem
    # Remove trailing numbers
    stem = re.sub(r"\d+$", "", stem)
    # Replace underscores/hyphens with spaces
    keyword = re.sub(r"[_-]", " ", stem)
    return keyword.strip().lower()


def generate_pin_text(text_provider: AzureFoundryTextProvider, channel: PinterestChannel, keyword: str) -> dict:
    """Generate title, tagline, and time text for a pin."""
    return text_provider.generate_text(
        niche="food",
        keyword=keyword,
        channel=channel,
        image_url="",
    )


def smart_crop_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize and crop image to target dimensions, preserving center content."""
    orig_w, orig_h = img.size
    target_ratio = target_w / target_h
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        # Image is wider - crop sides
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
    else:
        # Image is taller - crop top/bottom (favor keeping more top for food)
        new_h = int(orig_w / target_ratio)
        top = (orig_h - new_h) // 3  # Bias towards top
        img = img.crop((0, top, orig_w, top + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get Fredoka One font for Pinterest-style text."""
    font_path = Path(__file__).parent / "fonts" / "Fredoka-VariableFont.ttf"
    return ImageFont.truetype(str(font_path), size)


def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str = "white",
    outline: str = "black",
    outline_width: int = 3,
) -> None:
    """Draw text with an outline/stroke effect."""
    x, y = position

    # Draw outline by drawing text multiple times offset
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)

    # Draw main text
    draw.text(position, text, font=font, fill=fill)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        if bbox[2] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def create_pin(
    img_path: Path,
    title: str,
    tagline: str,
    time_text: str,
    output_path: Path,
) -> None:
    """Create a Pinterest pin with text overlay."""
    # Load and resize image
    img = Image.open(img_path).convert("RGB")
    img = smart_crop_resize(img, PIN_WIDTH, PIN_HEIGHT)

    draw = ImageDraw.Draw(img)

    # Font sizes
    title_font = get_font(72)
    tagline_font = get_font(42)
    time_font = get_font(48)

    padding = 40
    max_text_width = PIN_WIDTH - (padding * 2)

    # Draw title at top (wrapped if needed)
    title_lines = wrap_text(title, title_font, max_text_width)
    y_offset = 60

    for line in title_lines:
        bbox = title_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = (PIN_WIDTH - text_width) // 2
        draw_text_with_outline(draw, (x, y_offset), line, title_font, outline_width=4)
        y_offset += bbox[3] - bbox[1] + 10

    # Draw tagline near bottom
    tagline_y = PIN_HEIGHT - 200
    bbox = tagline_font.getbbox(tagline)
    text_width = bbox[2] - bbox[0]
    x = (PIN_WIDTH - text_width) // 2
    draw_text_with_outline(draw, (x, tagline_y), tagline, tagline_font,
                           fill="#FFD700", outline_width=3)  # Gold color

    # Draw time text at bottom
    time_y = PIN_HEIGHT - 120
    bbox = time_font.getbbox(time_text)
    text_width = bbox[2] - bbox[0]
    x = (PIN_WIDTH - text_width) // 2
    draw_text_with_outline(draw, (x, time_y), time_text, time_font,
                           fill="#FFD700", outline_width=3)  # Gold color

    # Save with high quality
    img.save(output_path, "JPEG", quality=95)


def main():
    if len(sys.argv) < 2:
        print("Usage: python pin_maker.py <folder_path>")
        sys.exit(1)

    input_folder = Path(sys.argv[1])
    if not input_folder.is_dir():
        print(f"Error: {input_folder} is not a directory")
        sys.exit(1)

    # Setup output folder
    output_folder = input_folder / "output"
    output_folder.mkdir(exist_ok=True)

    # Load settings and create providers
    settings = load_dev_settings()
    azure_client = AzureOpenAI(
        azure_endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_api_key,
        api_version=settings.azure_foundry_api_version,
    )
    text_provider = AzureFoundryTextProvider(azure_client)
    channel = PinterestChannel(PROMPT)

    # Find all JPGs
    jpg_files = list(input_folder.glob("*.jpg")) + list(input_folder.glob("*.JPG"))
    jpg_files += list(input_folder.glob("*.jpeg")) + list(input_folder.glob("*.JPEG"))

    if not jpg_files:
        print(f"No JPG files found in {input_folder}")
        sys.exit(1)

    print(f"Found {len(jpg_files)} images to process")

    for img_path in jpg_files:
        keyword = extract_keyword(img_path.name)
        print(f"Processing: {img_path.name} -> keyword: '{keyword}'")

        try:
            # Generate text
            pin_text = generate_pin_text(text_provider, channel, keyword)
            print(f"  Title: {pin_text['title']}")
            print(f"  Tagline: {pin_text['tagline']}")
            print(f"  Time: {pin_text['time_text']}")

            # Create pin
            output_path = output_folder / f"pin_{img_path.stem}.jpg"
            create_pin(
                img_path,
                pin_text["title"],
                pin_text["tagline"],
                pin_text["time_text"],
                output_path,
            )
            print(f"  Saved: {output_path}")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"\nDone! Pins saved to {output_folder}")


if __name__ == "__main__":
    main()
