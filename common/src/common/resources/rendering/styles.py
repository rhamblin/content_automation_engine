"""Style registry - 15 Pinterest-optimized pin styles."""

from common.contracts.models import ImageOverlay, TextElement, VisualStyle

BRAND_TEXT = "chefexotic.com"

STYLES: dict[str, VisualStyle] = {
    # RIBBON BOX - White box with red ribbon prefix, large serif title
    "ribbon_box": VisualStyle(
        name="ribbon_box",
        description="White box with red ribbon banner and bold serif title. Clean editorial look.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=28,
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
            max_width_pct=0.65,
            max_lines=1,
        ),
        watermark=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=40,
            color="#FFFFFF",
            y_position=-80,
            alignment="right",
            outline_width=0,
        ),
        overlays=[
            ImageOverlay(
                position="box",
                color="#FFFFFF",
                opacity=0.88,
                height_pct=0.35,
                y_position=700,
                width_pct=0.78,
                border_color="#cccccc",
                border_width=1,
            ),
            ImageOverlay(
                position="box",
                color="#d63031",
                opacity=0.95,
                height_pct=0.035,
                y_position=530,
                width_pct=0.42,
                shape="ribbon",
                notch_pct=0.04,
            ),
        ],
    ),
    # SLAB SCRIPT - Full-width band with bold slab title + flowing script accent
    "slab_script": VisualStyle(
        name="slab_script",
        description="Full-width cream band with bold brown title and pink script accent. Warm, homestyle feel.",
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=100,
            color="#7B3F00",
            y_position=640,
            outline_width=0,
            max_lines=1,
        ),
        accent=TextElement(
            font_file="DancingScript.ttf",
            font_size=90,
            color="#C2185B",
            y_position=740,
            outline_width=0,
        ),
        watermark=TextElement(
            font_file="DancingScript.ttf",
            font_size=40,
            color="#FFFFFF",
            y_position=-80,
            alignment="right",
            outline_width=0,
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.78,
                height_pct=0.2,
                y_position=710,
                border_color="#5C3A1E",
                border_width=2,
            ),
        ],
    ),
    # EDITORIAL CARD - White card with thin border, small caps prefix, large serif title
    "editorial_card": VisualStyle(
        name="editorial_card",
        description="White card with thin border, spaced caps prefix, and large serif title. Magazine editorial feel.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=24,
            color="#555555",
            y_position=640,
            outline_width=0,
        ),
        title=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=105,
            color="#1a1a1a",
            y_position=700,
            outline_width=0,
            max_width_pct=0.75,
            max_lines=1,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=40,
            color="#FFFFFF",
            y_position=-80,
            alignment="right",
            outline_width=0,
        ),
        overlays=[
            ImageOverlay(
                position="box",
                color="#FFFFFF",
                opacity=0.94,
                height_pct=0.32,
                y_position=770,
                width_pct=0.85,
                border_color="#1a1a1a",
                border_width=2,
            ),
        ],
    ),
    # BOLD BAND - Full-width white band with gold lines, bold title, olive caps prefix + tagline
    "bold_band": VisualStyle(
        name="bold_band",
        description="Full-width white band with gold border lines, massive bold title, olive caps prefix and tagline.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=30,
            color="#4A5520",
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
            font_size=28,
            color="#4A5520",
            y_position=850,
            outline_width=0,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=40,
            color="#FFFFFF",
            y_position=-80,
            alignment="right",
            outline_width=0,
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.95,
                height_pct=0.22,
                y_position=750,
                border_color="#9B8C4E",
                border_width=3,
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
