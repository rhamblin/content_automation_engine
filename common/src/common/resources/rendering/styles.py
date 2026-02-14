"""Style registry - Pinterest-optimized pin styles for mobile readability."""

from common.contracts.models import ImageOverlay, TextElement, VisualStyle

BRAND_TEXT = "chefexotic.com"

STYLES: dict[str, VisualStyle] = {
    # RIBBON BOX - White box with red ribbon prefix, large serif title
    "ribbon_box": VisualStyle(
        name="ribbon_box",
        description="White card with red ribbon banner above a bold serif title. The ribbon holds a short descriptor, the card holds the main title. Clean editorial look with strong contrast.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="#FFFFFF",
            y_position=520,
            outline_width=0,
        ),
        title=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=120,
            color="#1a1a1a",
            y_position=600,
            outline_width=0,
            max_width_pct=0.70,
            max_lines=1,
        ),
        watermark=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#000000",
        ),
        overlays=[
            ImageOverlay(
                position="box",
                color="#FFFFFF",
                opacity=0.92,
                height_pct=0.35,
                y_position=700,
                width_pct=0.82,
                border_color="#cccccc",
                border_width=2,
            ),
            ImageOverlay(
                position="box",
                color="#d63031",
                opacity=0.95,
                height_pct=0.04,
                y_position=530,
                width_pct=0.45,
                shape="ribbon",
                notch_pct=0.04,
            ),
        ],
    ),
    # SLAB SCRIPT - Full-width band with bold slab title + flowing script accent
    "slab_script": VisualStyle(
        name="slab_script",
        description="Full-width cream band with bold brown slab-serif title and a warm script accent line below. The title is the hero, the accent adds an elegant detail like an ingredient or flavor note.",
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=110,
            color="#5C3A1E",
            y_position=620,
            outline_width=0,
            max_lines=1,
        ),
        accent=TextElement(
            font_file="DancingScript.ttf",
            font_size=72,
            color="#C2185B",
            y_position=740,
            outline_width=1,
            outline_color="#FFFFFF",
        ),
        watermark=TextElement(
            font_file="DancingScript.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#5C3A1E",
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.88,
                height_pct=0.22,
                y_position=710,
                border_color="#5C3A1E",
                border_width=3,
            ),
        ],
    ),
    # EDITORIAL CARD - White card with thin border, small caps prefix, large serif title
    "editorial_card": VisualStyle(
        name="editorial_card",
        description="White card with thin dark border, uppercase prefix above and a large serif title. Magazine editorial feel. Prefix is a short category or time label, title is the main dish name.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="#333333",
            y_position=640,
            outline_width=0,
        ),
        title=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=105,
            color="#1a1a1a",
            y_position=700,
            outline_width=0,
            max_width_pct=0.78,
            max_lines=1,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#000000",
        ),
        overlays=[
            ImageOverlay(
                position="box",
                color="#FFFFFF",
                opacity=0.94,
                height_pct=0.32,
                y_position=770,
                width_pct=0.88,
                border_color="#1a1a1a",
                border_width=3,
            ),
        ],
    ),
    # BOLD BAND - Full-width white band with gold lines, bold title, olive caps prefix + tagline
    "bold_band": VisualStyle(
        name="bold_band",
        description="Full-width white band with gold border lines, massive bold title in the center, an uppercase prefix above and a tagline below. Prefix is a short label, tagline highlights a benefit or occasion.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=38,
            color="#3D4A1A",
            y_position=640,
            outline_width=0,
        ),
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=140,
            color="#1a1a1a",
            y_position=700,
            outline_width=0,
            max_lines=1,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="#3D4A1A",
            y_position=850,
            outline_width=0,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#000000",
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.95,
                height_pct=0.24,
                y_position=750,
                border_color="#9B8C4E",
                border_width=4,
            ),
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
