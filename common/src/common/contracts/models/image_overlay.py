"""ImageOverlay - Self-applying gradient/solid overlay for images."""

from dataclasses import dataclass

from PIL import Image, ImageDraw


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
    angle: int = 0  # rotation in degrees (for center/box)

    def apply(self, img: Image.Image) -> Image.Image:
        overlay_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)

        h = int(img.height * self.height_pct)
        alpha = int(255 * self.opacity)

        rgb = tuple(int(self.color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

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
            draw.rectangle([0, top_y, img.width, bot_y], fill=(*rgb, alpha))
            if self.border_width > 0:
                border_rgb = tuple(int(self.border_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
                draw.rectangle([0, top_y, img.width, bot_y], outline=(*border_rgb, 255), width=self.border_width)
        elif self.position == "box":
            w = int(img.width * self.width_pct)
            center_x = img.width // 2
            left = center_x - w // 2
            right = center_x + w // 2
            top_y = center_y - h // 2
            bot_y = center_y + h // 2
            draw.rectangle([left, top_y, right, bot_y], fill=(*rgb, alpha))
            if self.border_width > 0:
                border_rgb = tuple(int(self.border_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
                draw.rectangle([left, top_y, right, bot_y], outline=(*border_rgb, 255), width=self.border_width)
        else:  # full
            draw.rectangle([0, 0, img.width, img.height], fill=(*rgb, alpha))

        # Rotate overlay for center/box if angle specified
        if self.angle != 0 and self.position in ["center", "box"]:
            overlay_img = overlay_img.rotate(self.angle, resample=Image.Resampling.BICUBIC,
                                              center=(img.width // 2, center_y))

        return Image.alpha_composite(img.convert("RGBA"), overlay_img).convert("RGB")
