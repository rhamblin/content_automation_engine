"""Layout - Defines how the source image is composed onto the canvas."""

from dataclasses import dataclass


@dataclass
class Layout:
    """Controls how the source image is placed on the canvas before overlays/text.

    Layout types:
        single           - Default full-canvas crop (current behavior).
        split_duplicate  - Same image cropped into top + bottom regions.
        split_horizontal - Left/right split (single source).
        grid_2x2         - 2x2 grid of the same image.
        image_over_color - Image on top, solid color on bottom.
        color_over_image - Solid color on top, image on bottom.
    """

    type: str = "single"
    split_pct: float = 0.5
    gap: int = 0
    color: str = "#000000"
    crop_focus_top: str = "center"
    crop_focus_bottom: str = "center"

    @classmethod
    def from_dict(cls, data: dict | None) -> "Layout":
        if not data:
            return cls()
        return cls(
            type=data.get("type", "single"),
            split_pct=data.get("split_pct", 0.5),
            gap=data.get("gap", 0),
            color=data.get("color", "#000000"),
            crop_focus_top=data.get("crop_focus_top", "center"),
            crop_focus_bottom=data.get("crop_focus_bottom", "center"),
        )
