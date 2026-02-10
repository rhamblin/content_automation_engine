"""Style registry - Predefined pin styles and helpers."""

from image_overlay import ImageOverlay
from pin_style import PinStyle
from text_element import TextElement

BRAND_TEXT = "chefexotic.com"

# =============================================================================
# Predefined Styles
# =============================================================================

STYLES: dict[str, PinStyle] = {
    "bold_rustic": PinStyle(
        name="bold_rustic",
        description="Bold slab serif with gold accents. Great for comfort food and hearty dishes.",
        mood=["comfort", "hearty", "homestyle", "rustic"],
        title=TextElement(
            font_file="nexa-rust.slab-black-shadow-01.otf",
            font_size=110,
            color="white",
            y_position=60,
            outline_width=6,
        ),
        tagline=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=52,
            color="#FFD700",
            y_position=-180,
            outline_width=5,
        ),
        time_text=TextElement(
            font_file="Allura-Regular.ttf",
            font_size=72,
            color="#FFD700",
            y_position=-100,
            outline_width=5,
        ),
        watermark=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=24,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.25, height_pct=0.35),
    ),
    "script_elegant": PinStyle(
        name="script_elegant",
        description="Elegant script accents with clean title. Best for gourmet and date night dishes.",
        mood=["elegant", "gourmet", "romantic", "upscale"],
        title=TextElement(
            font_file="nexa-rust.slab-black-shadow-01.otf",
            font_size=100,
            color="white",
            y_position=70,
            outline_width=5,
        ),
        accent=TextElement(
            font_file="Allura-Regular.ttf",
            font_size=72,
            color="#FFD700",
            y_position=180,
            outline_width=4,
        ),
        tagline=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=42,
            color="white",
            y_position=-120,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.3, height_pct=0.4),
    ),
    "quick_easy": PinStyle(
        name="quick_easy",
        description="Script prefix with bold title. Perfect for quick weeknight meals.",
        mood=["quick", "easy", "weeknight", "simple"],
        prefix=TextElement(
            font_file="Allura-Regular.ttf",
            font_size=64,
            color="#FFD700",
            y_position=40,
            outline_width=4,
        ),
        title=TextElement(
            font_file="nexa-rust.slab-black-shadow-01.otf",
            font_size=95,
            color="white",
            y_position=110,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=48,
            color="white",
            y_position=-150,
            outline_width=5,
            banner_color="rgba(0,0,0,0.5)",
            banner_padding=15,
        ),
        watermark=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=24,
            color="white",
            corner="bottom_left",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.4),
    ),
    "bottom_stack": PinStyle(
        name="bottom_stack",
        description="Text stacked at bottom. Good for beautiful plated dishes where food is the star.",
        mood=["beautiful", "plated", "restaurant", "showcase"],
        title=TextElement(
            font_file="nexa-rust.slab-black-shadow-01.otf",
            font_size=100,
            color="white",
            y_position=-280,
            outline_width=6,
        ),
        tagline=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=44,
            color="#FFD700",
            y_position=-180,
            outline_width=4,
        ),
        time_text=TextElement(
            font_file="Allura-Regular.ttf",
            font_size=60,
            color="white",
            y_position=-110,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=24,
            color="white",
            corner="top_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="bottom", opacity=0.45, height_pct=0.5),
    ),
    "clean_minimal": PinStyle(
        name="clean_minimal",
        description="Clean, minimal look. Ideal for healthy, fresh, light recipes.",
        mood=["healthy", "fresh", "light", "clean", "minimal"],
        title=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=85,
            color="white",
            y_position=60,
            outline_width=4,
        ),
        tagline=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=40,
            color="white",
            y_position=160,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Fredoka-VariableFont.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.2, height_pct=0.3),
    ),
}


def get_style(name: str) -> PinStyle:
    """Get a style by name."""
    if name not in STYLES:
        raise KeyError(f"Style '{name}' not found. Available: {list(STYLES.keys())}")
    return STYLES[name]


def get_style_brief() -> str:
    """Generate style options for LLM prompt."""
    lines = ["Available styles:"]
    for name, style in STYLES.items():
        lines.append(f'- "{name}": {style.description} (mood: {", ".join(style.mood)})')
    return "\n".join(lines)


def list_styles() -> list[str]:
    """Return available style names."""
    return list(STYLES.keys())
