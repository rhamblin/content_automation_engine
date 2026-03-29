"""BgRemoverService — pure image transform, no file I/O.

Pipeline: source image -> remove background -> crop -> scale -> colored canvas -> gradient tint.
"""

from PIL import Image, ImageDraw

from common.app_logger import AppLogger

logger = AppLogger(__name__)

CANVAS_W, CANVAS_H = 1000, 1500
SUBJECT_AREA_PCT = 0.90
GRADIENT_MAX_ALPHA = 120


class BgRemoverService:
    """Stateless service: remove background and place on colored canvas."""

    def process(
        self,
        source: Image.Image,
        background_color: str,
        source_name: str = "",
    ) -> Image.Image | None:
        """Remove background, place subject on colored canvas with gradient.

        Args:
            source: RGB/RGBA source image.
            background_color: Hex color string (e.g. "#FFB6C1").
            source_name: Optional filename for logging.

        Returns:
            Final RGB image on colored canvas, or None on failure.
        """
        try:
            return self._pipeline(source, background_color, source_name)
        except Exception as e:
            logger.error("bg-remove failed for '%s': %s", source_name, e)
            return None

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _pipeline(
        self, source: Image.Image, bg_color: str, name: str
    ) -> Image.Image:
        from rembg import remove  # lazy import — heavy dependency

        # 1. Remove background
        rgba = remove(source.convert("RGBA"))
        logger.info("Background removed: %s", name)

        # 2. Crop to bounding box of non-transparent pixels
        bbox = rgba.getbbox()
        if bbox is None:
            raise ValueError("Image is fully transparent after bg removal")
        cropped = rgba.crop(bbox)

        # 3. Scale subject to fit canvas (90% area, preserve aspect ratio)
        max_w = int(CANVAS_W * SUBJECT_AREA_PCT)
        max_h = int(CANVAS_H * SUBJECT_AREA_PCT)
        scale = min(max_w / cropped.width, max_h / cropped.height)
        new_w = int(cropped.width * scale)
        new_h = int(cropped.height * scale)
        subject = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 4. Create solid-color canvas and paste subject centered
        rgb = self._parse_rgb(bg_color)
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (*rgb, 255))
        paste_x = (CANVAS_W - new_w) // 2
        paste_y = (CANVAS_H - new_h) // 2
        canvas.paste(subject, (paste_x, paste_y), subject)

        # 5. Apply top-to-bottom gradient tint
        canvas = self._apply_gradient(canvas, rgb)

        return canvas.convert("RGB")

    @staticmethod
    def _apply_gradient(canvas: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
        """Top-to-bottom gradient overlay: alpha 0 at top -> GRADIENT_MAX_ALPHA at bottom."""
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for y in range(canvas.height):
            alpha = int(GRADIENT_MAX_ALPHA * y / canvas.height)
            draw.line([(0, y), (canvas.width, y)], fill=(*rgb, alpha))
        return Image.alpha_composite(canvas, overlay)

    @staticmethod
    def _parse_rgb(hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
