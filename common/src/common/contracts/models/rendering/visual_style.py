"""VisualStyle - Complete visual style definition for image-based content."""

from dataclasses import dataclass, field

from .image_overlay import ImageOverlay
from .layout import Layout
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
    layout: Layout = field(default_factory=Layout)
    overlays: list[ImageOverlay] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "VisualStyle":
        """Deserialize from JSON config or DB visual_styles.spec dict.

        Accepts either:
          - Full config: {"name": ..., "description": ..., "spec": {"title": {...}, ...}}
          - Spec-only: {"title": {...}, "watermark": {...}, ...}
        """
        spec = data.get("spec", data)
        text_keys = ("title", "watermark", "prefix", "accent", "tagline")
        elements = {}
        for key in text_keys:
            if key in spec and spec[key] is not None:
                elements[key] = TextElement.from_dict(spec[key])
        overlays = [ImageOverlay.from_dict(o) for o in spec.get("overlays", [])]
        layout = Layout.from_dict(spec.get("layout"))
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            layout=layout,
            overlays=overlays,
            **elements,
        )

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
        "title": (
            '"title": "Short punchy title, 2-4 words, ALL CAPS, no emoji"',
            "Title MUST be plain text, no emoji/unicode symbols. Use power words that trigger clicks: Easy, Best, Perfect, Ultimate, Crispy, Creamy, Loaded. Keep it under 25 characters",
        ),
        "tagline": (
            '"tagline": "Punchy 3-word phrase, ALL CAPS, no emoji"',
            "Tagline is exactly 3 punchy words. MUST be unique and specific to the content - never repeat generic phrases. Vary the angle: craving trigger (MELT IN MOUTH, CRISPY GOLDEN BITES), occasion (DATE NIGHT WINNER, SUNDAY BRUNCH HERO), ease (JUST FIVE STEPS, ONE PAN MAGIC), or bold claim (FLAVOR BOMB ALERT, BETTER THAN TAKEOUT). Plain text only, no emoji",
        ),
        "prefix": (
            '"prefix": "Short label, 1-3 words, ALL CAPS, no emoji"',
            "Prefix is a time or category label (e.g., 30-MINUTE, QUICK & EASY, ONE-POT, WEEKNIGHT). Plain text only, no emoji",
        ),
        "accent": (
            '"accent": "Elegant detail, 2-4 words, Title Case, no emoji"',
            "Accent adds a flavor or ingredient detail (e.g., with Garlic Butter, Crispy Golden Crust). Plain text only, no emoji",
        ),
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
