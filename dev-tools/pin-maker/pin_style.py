"""PinStyle - Complete pin style definition combining text elements and overlay."""

from dataclasses import dataclass

from image_overlay import ImageOverlay
from text_element import TextElement


@dataclass
class PinStyle:
    """Complete pin style definition."""

    name: str
    description: str
    mood: list[str]
    title: TextElement
    watermark: TextElement
    prefix: TextElement | None = None
    accent: TextElement | None = None
    tagline: TextElement | None = None
    time_text: TextElement | None = None
    overlay: ImageOverlay | None = None

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
