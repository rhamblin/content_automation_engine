"""ImageOverlay - Self-applying gradient/solid overlay for images."""

from dataclasses import dataclass

from PIL import Image, ImageDraw


@dataclass
class ImageOverlay:
    """Gradient/solid overlay that knows how to apply itself."""

    position: str = "top"  # "top", "bottom", "full", "center", "box"
    color: str = "black"
    opacity: float = 0.3
    height_pct: float = 0.35
    center_y_pct: float = 0.5  # vertical center for "center" and "box"
    width_pct: float = 0.7  # box width as % of image (for "box" only)
    border_color: str | None = None  # box border color (for "box" only)
    border_width: int = 0  # box border width (for "box" only)

    def apply(self, img: Image.Image) -> Image.Image:
        overlay_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)

        h = int(img.height * self.height_pct)
        alpha = int(255 * self.opacity)

        if self.color == "black":
            rgb = (0, 0, 0)
        else:
            rgb = tuple(int(self.color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

        if self.position == "top":
            for i in range(h):
                draw.line([(0, i), (img.width, i)], fill=(*rgb, int(alpha * (1 - i / h))))
        elif self.position == "bottom":
            for i in range(h):
                y = img.height - h + i
                draw.line([(0, y), (img.width, y)], fill=(*rgb, int(alpha * i / h)))
        elif self.position == "center":
            center_y = int(img.height * self.center_y_pct)
            top_y = center_y - h // 2
            bot_y = center_y + h // 2
            draw.rectangle([0, top_y, img.width, bot_y], fill=(*rgb, alpha))
        elif self.position == "box":
            w = int(img.width * self.width_pct)
            center_y = int(img.height * self.center_y_pct)
            center_x = img.width // 2
            left = center_x - w // 2
            right = center_x + w // 2
            top_y = center_y - h // 2
            bot_y = center_y + h // 2
            draw.rectangle([left, top_y, right, bot_y], fill=(*rgb, alpha))
            if self.border_color and self.border_width > 0:
                border_rgb = tuple(int(self.border_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
                draw.rectangle([left, top_y, right, bot_y], outline=(*border_rgb, 255), width=self.border_width)
        else:  # full
            draw.rectangle([0, 0, img.width, img.height], fill=(*rgb, alpha))

        return Image.alpha_composite(img.convert("RGBA"), overlay_img).convert("RGB")
