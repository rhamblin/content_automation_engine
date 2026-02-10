"""TextElement - Self-rendering text block for visual content overlays."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = Path(__file__).parent.parent.parent / "resources" / "fonts"


@dataclass
class TextElement:
    """Text block that knows how to render itself."""

    font_file: str
    font_size: int
    color: str
    y_position: int | None = None  # positive=from top, negative=from bottom
    corner: str | None = None  # "bottom_right", "top_left", etc.
    outline_width: int = 0
    outline_color: str = "black"
    alignment: str = "center"  # "center", "left", "right"
    banner_color: str | None = None
    banner_padding: int = 12
    banner_full_width: bool = False  # True = banner spans entire image width
    banner_border_color: str | None = None  # Thin line on top/bottom edges
    banner_border_width: int = 2
    max_width_pct: float = 0.85

    def _get_font(self) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(FONTS_DIR / self.font_file), self.font_size)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        words = text.split()
        lines, current = [], []
        for word in words:
            test = " ".join(current + [word])
            if font.getbbox(test)[2] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def draw(
        self,
        canvas: ImageDraw.ImageDraw,
        text: str,
        img_width: int,
        img_height: int,
        base_img: Image.Image | None = None,
    ) -> Image.Image | None:
        """Draw text element. Returns modified image if banner with alpha was drawn."""
        font = self._get_font()
        margin = int(img_width * (1 - self.max_width_pct) / 2)

        # Calculate starting y
        if self.corner:
            bbox = font.getbbox(text)
            text_h = bbox[3] - bbox[1]
            y = margin if "top" in self.corner else img_height - text_h - margin
        else:
            y = self.y_position if self.y_position >= 0 else img_height + self.y_position

        # Wrap text (skip for corner elements)
        lines = [text] if self.corner else self._wrap_text(text, font, int(img_width * self.max_width_pct))

        result_img = None

        for line in lines:
            bbox = font.getbbox(line)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Calculate x
            if self.corner:
                x = margin if "left" in self.corner else img_width - text_w - margin
            else:
                x = {
                    "center": (img_width - text_w) // 2,
                    "left": margin,
                    "right": img_width - text_w - margin,
                }[self.alignment]

            # Banner - use alpha compositing for transparency
            if self.banner_color and base_img is not None:
                p = self.banner_padding
                overlay = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                if self.banner_full_width:
                    top_y = y - p
                    bot_y = y + text_h + p
                    overlay_draw.rectangle([0, top_y, img_width, bot_y], fill=self.banner_color)
                    # Border lines on edges
                    if self.banner_border_color:
                        bw = self.banner_border_width
                        overlay_draw.rectangle([0, top_y, img_width, top_y + bw], fill=self.banner_border_color)
                        overlay_draw.rectangle([0, bot_y - bw, img_width, bot_y], fill=self.banner_border_color)
                else:
                    overlay_draw.rectangle([x - p, y - p, x + text_w + p, y + text_h + p], fill=self.banner_color)
                base_img = Image.alpha_composite(base_img, overlay)
                result_img = base_img
                canvas = ImageDraw.Draw(base_img)

            # Outline
            if self.outline_width > 0:
                for dx in range(-self.outline_width, self.outline_width + 1):
                    for dy in range(-self.outline_width, self.outline_width + 1):
                        if dx != 0 or dy != 0:
                            canvas.text((x + dx, y + dy), line, font=font, fill=self.outline_color)

            # Text
            canvas.text((x, y), line, font=font, fill=self.color)
            y += text_h + 10

        return result_img
