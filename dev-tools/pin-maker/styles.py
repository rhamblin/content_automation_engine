"""Style registry - 15 Pinterest-optimized pin styles."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.contracts.models import ImageOverlay, TextElement, VisualStyle

BRAND_TEXT = "chefexotic.com"

# =============================================================================
# 15 Pinterest Viral-Optimized Styles
# =============================================================================

STYLES: dict[str, VisualStyle] = {
    # 1. BOLD RUSTIC - Textured slab + flowing script
    "bold_rustic": VisualStyle(
        name="bold_rustic",
        description="Textured slab with gold script accents. Perfect for comfort food and hearty dishes.",
        title=TextElement(
            font_file="NexaRust.otf",
            font_size=105,
            color="white",
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
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.3, height_pct=0.4),
    ),

    # 2. ELEGANT SCRIPT - Serif title + elegant script accent
    "elegant_script": VisualStyle(
        name="elegant_script",
        description="Elegant serif with flowing script. Best for gourmet and date night dishes.",
        title=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=95,
            color="white",
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
            color="white",
            y_position=-130,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.45),
    ),

    # 3. QUICK & EASY - Script prefix + bold condensed
    "quick_easy": VisualStyle(
        name="quick_easy",
        description="Script prefix with bold title. Perfect for quick weeknight meals.",
        prefix=TextElement(
            font_file="Sacramento.ttf",
            font_size=58,
            color="#FFD700",
            y_position=50,
            outline_width=3,
        ),
        title=TextElement(
            font_file="Oswald.ttf",
            font_size=90,
            color="white",
            y_position=120,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=42,
            color="white",
            y_position=-140,
            outline_width=4,
            banner_color=(0, 0, 0, 128),
            banner_padding=12,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_left",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.4),
    ),

    # 4. MODERN CLEAN - Minimal sans-serif
    "modern_clean": VisualStyle(
        name="modern_clean",
        description="Clean minimal sans-serif. Ideal for healthy, fresh, light recipes.",
        title=TextElement(
            font_file="Montserrat.ttf",
            font_size=80,
            color="white",
            y_position=70,
            outline_width=4,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="white",
            y_position=170,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.25, height_pct=0.35),
    ),

    # 5. RETRO FUN - Lobster + Righteous
    "retro_fun": VisualStyle(
        name="retro_fun",
        description="Retro script with rounded accents. Great for casual, fun recipes.",
        title=TextElement(
            font_file="Lobster.ttf",
            font_size=90,
            color="white",
            y_position=70,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="Righteous.ttf",
            font_size=44,
            color="#FF6B6B",
            y_position=-150,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Righteous.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.3, height_pct=0.35),
    ),

    # 6. DRAMATIC SERIF - Abril Fatface headlines
    "dramatic_serif": VisualStyle(
        name="dramatic_serif",
        description="Bold dramatic serif. Perfect for gourmet and restaurant-style dishes.",
        title=TextElement(
            font_file="AbrilFatface.ttf",
            font_size=95,
            color="white",
            y_position=80,
            outline_width=4,
        ),
        tagline=TextElement(
            font_file="Lora.ttf",
            font_size=40,
            color="#E8D5B7",
            y_position=-140,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Lora.ttf",
            font_size=20,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.4, height_pct=0.45),
    ),

    # 7. ALL CAPS IMPACT - Bebas Neue stacked
    "all_caps_impact": VisualStyle(
        name="all_caps_impact",
        description="Bold all-caps stacked text. High impact for viral potential.",
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=110,
            color="white",
            y_position=60,
            outline_width=6,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=38,
            color="#FFD700",
            y_position=-150,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.4),
    ),

    # 8. FRIENDLY CASUAL - Pacifico + Montserrat
    "friendly_casual": VisualStyle(
        name="friendly_casual",
        description="Friendly script with clean body. Perfect blogger aesthetic.",
        title=TextElement(
            font_file="Pacifico.ttf",
            font_size=85,
            color="white",
            y_position=70,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=40,
            color="white",
            y_position=-140,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.3, height_pct=0.4),
    ),

    # 9. PLAYFUL BOLD - Bangers comic style
    "playful_bold": VisualStyle(
        name="playful_bold",
        description="Comic-style bold. Great for desserts, kids recipes, fun food.",
        title=TextElement(
            font_file="Bangers.ttf",
            font_size=100,
            color="white",
            y_position=70,
            outline_width=6,
            outline_color="#FF4444",
        ),
        tagline=TextElement(
            font_file="DancingScript.ttf",
            font_size=48,
            color="#FFE135",
            y_position=-150,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.25, height_pct=0.35),
    ),

    # 10. CLASSIC COOKBOOK - Merriweather + Sacramento
    "classic_cookbook": VisualStyle(
        name="classic_cookbook",
        description="Traditional cookbook feel. Perfect for classic, timeless recipes.",
        title=TextElement(
            font_file="Merriweather.ttf",
            font_size=85,
            color="white",
            y_position=80,
            outline_width=4,
        ),
        accent=TextElement(
            font_file="Sacramento.ttf",
            font_size=55,
            color="#C9A962",
            y_position=185,
            outline_width=3,
        ),
        tagline=TextElement(
            font_file="Merriweather.ttf",
            font_size=34,
            color="white",
            y_position=-130,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.45),
    ),

    # 11. HANDMADE MARKER - PermanentMarker
    "handmade_marker": VisualStyle(
        name="handmade_marker",
        description="Hand-drawn marker style. Perfect for DIY, homemade, craft recipes.",
        title=TextElement(
            font_file="PermanentMarker.ttf",
            font_size=85,
            color="white",
            y_position=70,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=40,
            color="#98D8AA",
            y_position=-150,
            outline_width=4,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.3, height_pct=0.4),
    ),

    # 12. CONDENSED MODERN - Oswald + Sacramento
    "condensed_modern": VisualStyle(
        name="condensed_modern",
        description="Condensed sans with script accent. Modern food blog aesthetic.",
        prefix=TextElement(
            font_file="Sacramento.ttf",
            font_size=52,
            color="#FF9F43",
            y_position=45,
            outline_width=3,
        ),
        title=TextElement(
            font_file="Oswald.ttf",
            font_size=95,
            color="white",
            y_position=110,
            outline_width=5,
        ),
        tagline=TextElement(
            font_file="Oswald.ttf",
            font_size=36,
            color="white",
            y_position=-140,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=22,
            color="white",
            corner="bottom_left",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.4),
    ),

    # 13. ROMANTIC FLOWING - GreatVibes + Lora
    "romantic_flowing": VisualStyle(
        name="romantic_flowing",
        description="Flowing elegant script. Perfect for romantic and special occasions.",
        title=TextElement(
            font_file="GreatVibes.ttf",
            font_size=90,
            color="white",
            y_position=70,
            outline_width=4,
        ),
        tagline=TextElement(
            font_file="Lora.ttf",
            font_size=42,
            color="#F8B4D9",
            y_position=-140,
            outline_width=3,
        ),
        watermark=TextElement(
            font_file="Lora.ttf",
            font_size=20,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.35, height_pct=0.4),
    ),

    # 14. BOLD CONTRAST - Montserrat weight contrast
    "bold_contrast": VisualStyle(
        name="bold_contrast",
        description="Bold/light weight contrast. Contemporary, magazine-style look.",
        title=TextElement(
            font_file="Montserrat.ttf",
            font_size=90,
            color="white",
            y_position=70,
            outline_width=5,
        ),
        accent=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="#A8DADC",
            y_position=175,
            outline_width=2,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=38,
            color="white",
            y_position=-140,
            outline_width=3,
            banner_color=(0, 0, 0, 102),
            banner_padding=10,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="white",
            corner="bottom_right",
            outline_width=2,
        ),
        overlay=ImageOverlay(position="top", opacity=0.3, height_pct=0.4),
    ),

    # 15. CENTER BANNER - Full-width bars behind text (like Classic & Savory example)
    "center_banner": VisualStyle(
        name="center_banner",
        description="Full-width banner bars behind centered text. Clean, professional look.",
        prefix=TextElement(
            font_file="DancingScript.ttf",
            font_size=58,
            color="#C71585",
            y_position=680,
            outline_width=0,
            banner_color=(255, 255, 255, 200),
            banner_padding=6,
            banner_full_width=True,
        ),
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=85,
            color="#5D3A3A",
            y_position=760,
            outline_width=0,
            banner_color=(255, 255, 255, 200),
            banner_padding=6,
            banner_full_width=True,
        ),
        watermark=TextElement(
            font_file="Montserrat.ttf",
            font_size=20,
            color="#666666",
            corner="bottom_right",
            outline_width=0,
        ),
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
