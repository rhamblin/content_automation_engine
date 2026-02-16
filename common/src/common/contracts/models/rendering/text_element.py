"""TextElement - Self-rendering text block for visual content overlays."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = Path(__file__).parent.parent.parent.parent / "resources" / "rendering" / "fonts"


@dataclass
class TextElement:
    """Text block that knows how to render itself."""

    font_file: str
    font_size: int
    color: str
    y_position: int  # positive=from top, negative=from bottom
    outline_width: int = 0
    outline_color: str = "#000000"
    alignment: str = "center"  # "center", "left", "right"
    max_width_pct: float = 0.85
    max_lines: int = 2  # shrink font until text fits in this many lines
    angle: int = 0  # rotation in degrees (counter-clockwise)

    @classmethod
    def from_dict(cls, data: dict) -> "TextElement":
        return cls(**data)

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
        base_img: Image.Image | None = None,
    ) -> Image.Image | None:
        """Draw text element. Returns modified image if rotated."""
        max_width = int(img_width * self.max_width_pct)
        margin = int(img_width * (1 - self.max_width_pct) / 2)

        # Auto-shrink font to fit within max_lines
        font_size = self.font_size
        font = self._get_font(font_size)
        while font_size > 20:
            lines = self._wrap_text(text, font, max_width)
            if len(lines) <= self.max_lines:
                break
            font_size -= 4
            font = self._get_font(font_size)

        # Calculate y (positive=from top, negative=from bottom)
        y = self.y_position if self.y_position >= 0 else img_height + self.y_position

        lines = self._wrap_text(text, font, max_width)

        # Rotated text: draw on overlay, rotate, composite
        if self.angle != 0 and base_img is not None:
            overlay = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            self._draw_lines(overlay_draw, lines, font, img_width, margin, y)
            rotated = overlay.rotate(self.angle, resample=Image.Resampling.BICUBIC, center=(img_width // 2, y))
            return Image.alpha_composite(base_img, rotated)

        self._draw_lines(canvas, lines, font, img_width, margin, y)
        return None

    def _draw_lines(
        self,
        canvas: ImageDraw.ImageDraw,
        lines: list[str],
        font: ImageFont.FreeTypeFont,
        img_width: int,
        margin: int,
        y: int,
    ) -> None:
        """Draw text lines with outline."""
        for line in lines:
            bbox = font.getbbox(line)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            x = {
                "center": (img_width - text_w) // 2,
                "left": margin,
                "right": img_width - text_w - margin,
            }[self.alignment]

            if self.outline_width > 0:
                for dx in range(-self.outline_width, self.outline_width + 1):
                    for dy in range(-self.outline_width, self.outline_width + 1):
                        if dx != 0 or dy != 0:
                            canvas.text((x + dx, y + dy), line, font=font, fill=self.outline_color)

            canvas.text((x, y), line, font=font, fill=self.color)
            y += int(text_h) + 10
