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
                ("watermark", self.watermark),
            ]
            if el is not None
        ]

    # Field prompt info for LLM text generation
    FIELD_SCHEMA = {
        "title": ('"title": "Catchy title (2-4 words, ALL CAPS)"', None),
        "tagline": ('"tagline": "Benefit phrase (1-3 words, ALL CAPS or sentence case)"', "Tagline highlights ease, occasion, or benefit"),
        "prefix": ('"prefix": "Descriptor prefix (e.g., Quick & Easy, 30-Minute)"', "Prefix is time-based or descriptor"),
        "accent": ('"accent": "Elegant sub-phrase (e.g., with Parmesan)"', "Accent adds elegant detail"),
    }

    def text_fields(self) -> list[str]:
        """Return field names that need LLM-generated text (excludes watermark)."""
        return [key for key, _ in self.elements() if key != "watermark"]

    def prompt_schema(self) -> tuple[list[str], list[str]]:
        """Return (field_lines, guidelines) for LLM prompt building."""
        fields = self.text_fields()
        field_lines = [self.FIELD_SCHEMA.get(f, (f'"{f}": "..."', None))[0] for f in fields]
        guidelines = [self.FIELD_SCHEMA[f][1] for f in fields if f in self.FIELD_SCHEMA and self.FIELD_SCHEMA[f][1]]
        return field_lines, guidelines
