"""TextElement - Self-rendering text block for visual content overlays."""

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageDraw, ImageFont

FONTS_DIR = Path(__file__).parent.parent.parent / "resources" / "fonts"


@dataclass
class TextElement:
    """Text block that knows how to render itself."""

    font_file: str
    font_size: int
    color: str
    y_position: int  # positive=from top, negative=from bottom
    outline_width: int = 0
    outline_color: str = "black"
    alignment: str = "center"  # "center", "left", "right"
    max_width_pct: float = 0.85

    def _get_font(self, size: int | None = None) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(FONTS_DIR / self.font_file), size or self.font_size)

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
    ) -> None:
        """Draw text element on canvas."""
        max_width = int(img_width * self.max_width_pct)
        margin = int(img_width * (1 - self.max_width_pct) / 2)

        # Auto-shrink font to fit within 2 lines
        font_size = self.font_size
        font = self._get_font(font_size)
        while font_size > 20:
            lines = self._wrap_text(text, font, max_width)
            if len(lines) <= 2:
                break
            font_size -= 4
            font = self._get_font(font_size)

        # Calculate y (positive=from top, negative=from bottom)
        y = self.y_position if self.y_position >= 0 else img_height + self.y_position

        lines = self._wrap_text(text, font, max_width)

        for line in lines:
            bbox = font.getbbox(line)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Calculate x based on alignment
            x = {
                "center": (img_width - text_w) // 2,
                "left": margin,
                "right": img_width - text_w - margin,
            }[self.alignment]

            # Outline
            if self.outline_width > 0:
                for dx in range(-self.outline_width, self.outline_width + 1):
                    for dy in range(-self.outline_width, self.outline_width + 1):
                        if dx != 0 or dy != 0:
                            canvas.text((x + dx, y + dy), line, font=font, fill=self.outline_color)

            # Text
            canvas.text((x, y), line, font=font, fill=self.color)
            y += text_h + 10
