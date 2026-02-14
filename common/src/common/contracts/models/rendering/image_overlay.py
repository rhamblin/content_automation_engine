"""ImageOverlay - Self-applying gradient/solid/shape/sticker overlay for images."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

STICKERS_DIR = Path(__file__).resolve().parents[3] / "resources" / "rendering" / "stickers"


@dataclass
class ImageOverlay:
    """Gradient/solid overlay that knows how to apply itself."""

    position: str = "top"  # "top", "bottom", "full", "center", "box"
    color: str = "#000000"
    opacity: float = 0.3
    height_pct: float = 0.35
    y_position: int = 750  # positive=from top, negative=from bottom (for center/box)
    width_pct: float = 0.7  # box width (for "box" only)
    border_color: str = "#000000"
    border_width: int = 0
    x_position: int = 0  # horizontal offset from center (positive=right, negative=left)
    angle: int = 0  # rotation in degrees (for center/box)
    shape: str = "rectangle"  # "rectangle", "ribbon", "pill", "sticker"
    notch_pct: float = 0.03  # ribbon notch depth as % of image width
    corner_radius: int = 20  # pill corner radius in pixels
    sticker_file: str | None = None  # e.g. "curved_arrow.png"
    flip_h: bool = False  # flip sticker horizontally
    flip_v: bool = False  # flip sticker vertically

    def _parse_rgb(self, hex_color: str) -> tuple[int, int, int]:
        return tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    def _draw_shape(self, draw: ImageDraw.Draw, left: int, top_y: int, right: int, bot_y: int,
                    fill: tuple, outline: tuple | None = None) -> None:
        """Draw the configured shape within the given bounding box."""
        if self.shape == "ribbon":
            notch = int((right - left) * self.notch_pct)
            cy = (top_y + bot_y) // 2
            points = [(left, top_y), (right, top_y), (right - notch, cy),
                      (right, bot_y), (left, bot_y), (left + notch, cy)]
            draw.polygon(points, fill=fill)
            if outline:
                draw.polygon(points, outline=outline, width=self.border_width)
        elif self.shape == "pill":
            draw.rounded_rectangle([left, top_y, right, bot_y], radius=self.corner_radius, fill=fill)
            if outline:
                draw.rounded_rectangle([left, top_y, right, bot_y], radius=self.corner_radius,
                                       outline=outline, width=self.border_width)
        else:  # rectangle
            draw.rectangle([left, top_y, right, bot_y], fill=fill)
            if outline:
                draw.rectangle([left, top_y, right, bot_y], outline=outline, width=self.border_width)

    def _apply_sticker(self, img: Image.Image) -> Image.Image:
        """Load, recolor, resize and composite a sticker PNG."""
        path = STICKERS_DIR / self.sticker_file
        sticker = Image.open(path).convert("RGBA")

        # Resize based on height_pct, maintain aspect ratio
        target_h = int(img.height * self.height_pct)
        ratio = target_h / sticker.height
        target_w = int(sticker.width * ratio)
        sticker = sticker.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Recolor
        r, g, b, a = sticker.split()
        gray = ImageOps.grayscale(sticker)
        rgb = self._parse_rgb(self.color)
        colored = ImageOps.colorize(gray, black=rgb, white=rgb)
        colored = colored.convert("RGBA")

        # Apply opacity
        a = a.point(lambda p: int(p * self.opacity))
        colored.putalpha(a)

        # Flip if needed
        if self.flip_h:
            colored = colored.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if self.flip_v:
            colored = colored.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        # Rotate if needed
        if self.angle != 0:
            colored = colored.rotate(self.angle, resample=Image.Resampling.BICUBIC, expand=True)

        # Position
        center_y = self.y_position if self.y_position >= 0 else img.height + self.y_position
        center_x = img.width // 2 + self.x_position
        paste_x = center_x - colored.width // 2
        paste_y = center_y - colored.height // 2

        result = img.convert("RGBA")
        result.paste(colored, (paste_x, paste_y), colored)
        return result.convert("RGB")

    def apply(self, img: Image.Image) -> Image.Image:
        if self.shape == "sticker" and self.sticker_file:
            return self._apply_sticker(img)

        overlay_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)

        h = int(img.height * self.height_pct)
        alpha = int(255 * self.opacity)
        rgb = self._parse_rgb(self.color)
        fill = (*rgb, alpha)

        border_outline = None
        if self.border_width > 0:
            border_rgb = self._parse_rgb(self.border_color)
            border_outline = (*border_rgb, 255)

        # Calculate y (positive=from top, negative=from bottom)
        center_y = self.y_position if self.y_position >= 0 else img.height + self.y_position

        if self.position == "top":
            for i in range(h):
                draw.line([(0, i), (img.width, i)], fill=(*rgb, int(alpha * (1 - i / h))))
        elif self.position == "bottom":
            for i in range(h):
                y = img.height - h + i
                draw.line([(0, y), (img.width, y)], fill=(*rgb, int(alpha * i / h)))
        elif self.position == "center":
            top_y = center_y - h // 2
            bot_y = center_y + h // 2
            x_off = self.x_position
            self._draw_shape(draw, 0 + x_off, top_y, img.width + x_off, bot_y, fill, border_outline)
        elif self.position == "box":
            w = int(img.width * self.width_pct)
            center_x = img.width // 2 + self.x_position
            left = center_x - w // 2
            right = center_x + w // 2
            top_y = center_y - h // 2
            bot_y = center_y + h // 2
            self._draw_shape(draw, left, top_y, right, bot_y, fill, border_outline)
        else:  # full
            draw.rectangle([0, 0, img.width, img.height], fill=fill)

        # Rotate overlay for center/box if angle specified
        if self.angle != 0 and self.position in ["center", "box"]:
            overlay_img = overlay_img.rotate(self.angle, resample=Image.Resampling.BICUBIC,
                                              center=(img.width // 2 + self.x_position, center_y))

        return Image.alpha_composite(img.convert("RGBA"), overlay_img).convert("RGB")
