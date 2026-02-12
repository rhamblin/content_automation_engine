"""VisualStyle - Complete visual style definition for image-based content."""

from dataclasses import dataclass, field

from .image_overlay import ImageOverlay
from .text_element import TextElement


@dataclass
class VisualStyle:
    """Complete visual style definition for image-based content (pins, posts, thumbnails)."""

    name: str
    description: str
    title: TextElement
    watermark: TextElement
    prefix: TextElement | None = None
    accent: TextElement | None = None
    tagline: TextElement | None = None
    time_text: TextElement | None = None
    overlays: list[ImageOverlay] = field(default_factory=list)

    def elements(self) -> list[tuple[str, TextElement]]:
        """Return (key, element) pairs in render order."""
        return [
            (key, el)
            for key, el in [
                ("prefix", self.prefix),
                ("title", self.title),
                ("accent", self.accent),
                ("tagline", self.tagline),
                ("time_text", self.time_text),
                ("watermark", self.watermark),
            ]
            if el is not None
        ]
