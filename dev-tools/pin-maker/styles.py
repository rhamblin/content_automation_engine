"""Style registry - 15 Pinterest-optimized pin styles."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.contracts.models import ImageOverlay, TextElement, VisualStyle

BRAND_TEXT = "chefexotic.com"

STYLES: dict[str, VisualStyle] = {
    # 1. BOLD RUSTIC - Textured slab + flowing script
    "bold_rustic": VisualStyle(
        name="bold_rustic",
        description="...",
        title=TextElement(
            font_file="NexaRust.otf",
            font_size=105,
            color="#FFFFFF",
            y_position=70,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="DancingScript.ttf",
            font_size=52,
            color="#FFD700",
            y_position=-160,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="GreatVibes.ttf",
            font_size=70,
            color="#ffffff",
            y_position=700,
            angle=45,
        ),
        overlays=[
            ImageOverlay(
                position="box",
                color="#000000",
                opacity=0.3,
                height_pct=0.4,
                y_position=750,
                border_color="#469832",
                border_width=4,
                angle=45,
                width_pct=0.7,
            )
        ],
    ),
    # 2. ELEGANT SCRIPT - Serif title + elegant script accent
    "elegant_script": VisualStyle(
        name="elegant_script",
        description="Elegant serif with flowing script. Best for gourmet and date night dishes.",
        title=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=95,
            color="#FFFFFF",
            y_position=80,
            outline_width=4,
        ),
        accent=TextElement(
            font_file="GreatVibes.ttf",
            font_size=68,
            color="#FFD700",
            y_position=190,
            outline_width=3,
        ),
        tagline=TextElement(
            font_file="Lora.ttf",
            font_size=38,
            color="#FFFFFF",
            y_position=-130,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="#FFFFFF",
            y_position=-50,
            alignment="right",
            outline_width=2,
        ),
        overlays=[ImageOverlay(position="top", opacity=0.35, height_pct=0.45)],
    ),
    # 15. CENTER BANNER - Full-width band behind centered text (like Classic & Savory example)
    "center_banner": VisualStyle(
        name="center_banner",
        description="Full-width banner band behind centered text. Clean, professional look.",
        prefix=TextElement(
            font_file="GreatVibes.ttf",
            font_size=72,
            color="#C71585",
            y_position=680,
            outline_width=0,
        ),
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=90,
            color="#5D3A3A",
            y_position=765,
            outline_width=0,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="#666666",
            y_position=-50,
            alignment="right",
            outline_width=0,
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.85,
                height_pct=0.18,
                y_position=750,
            )
        ],
    ),
}


def get_style(name: str) -> VisualStyle:
    """Get a style by name."""
    if name not in STYLES:
        raise KeyError(f"Style '{name}' not found. Available: {list(STYLES.keys())}")
    return STYLES[name]


def get_style_brief() -> str:
    """Generate style options for LLM prompt."""
    lines = ["Available styles:"]
    for name, style in STYLES.items():
        lines.append(f'- "{name}": {style.description}')
    return "\n".join(lines)


def list_styles() -> list[str]:
    """Return available style names."""
    return list(STYLES.keys())
