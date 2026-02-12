"""Style Explorer - Visual editor for Pinterest pin styles."""

import sys
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.contracts.models import ImageOverlay, TextElement, VisualStyle
from common.providers.distribution_channel.pinterest import PinterestChannel

from styles import BRAND_TEXT, STYLES

# Convert named colors to hex for Streamlit color_picker
COLOR_MAP = {
    "white": "#FFFFFF", "black": "#000000", "red": "#FF0000",
    "green": "#00FF00", "blue": "#0000FF", "yellow": "#FFFF00",
    "orange": "#FFA500", "pink": "#FFC0CB", "gray": "#808080",
}

def to_hex(color: str) -> str:
    return COLOR_MAP.get(color.lower(), color) if not color.startswith("#") else color

st.set_page_config(page_title="Style Explorer", layout="wide")
st.title("Style Explorer")

channel = PinterestChannel()

# Sidebar
st.sidebar.header("Image")
uploaded = st.sidebar.file_uploader("Upload", type=["jpg", "jpeg", "png"])
source_img = Image.open(uploaded).convert("RGB") if uploaded else Image.new("RGB", (1000, 1500), "#8B4513")

st.sidebar.header("Style")
style_name = st.sidebar.selectbox("Base style", list(STYLES.keys()))
base_style = STYLES[style_name]

st.sidebar.header("Text")
text_data = {
    "title": st.sidebar.text_input("Title", "Delicious Recipe"),
    "prefix": st.sidebar.text_input("Prefix", "Quick & Easy"),
    "tagline": st.sidebar.text_input("Tagline", "Perfect for dinner"),
    "accent": st.sidebar.text_input("Accent", "homemade"),
}

# Controls and Preview
col1, col2 = st.columns([1, 1])

with col1:
    # Overlay
    st.subheader("Overlay")
    ov = base_style.overlay
    if ov:
        ov_pos = st.selectbox("Position", ["top", "bottom", "center", "box", "full"],
                              index=["top", "bottom", "center", "box", "full"].index(ov.position))
        c1, c2 = st.columns(2)
        ov_color = c1.color_picker("Color", to_hex(ov.color))
        ov_opacity = c2.slider("Opacity", 0.0, 1.0, ov.opacity)
        c3, c4 = st.columns(2)
        ov_height = c3.slider("Height %", 0.05, 0.5, ov.height_pct)
        ov_center_y = c4.slider("Center Y %", 0.0, 1.0, ov.center_y_pct)

        ov_width, ov_border_color, ov_border_width = ov.width_pct, None, 0
        if ov_pos == "box":
            c5, c6, c7 = st.columns(3)
            ov_width = c5.slider("Width %", 0.3, 1.0, ov.width_pct)
            ov_border_color = c6.color_picker("Border", ov.border_color or "#333333")
            ov_border_width = c7.slider("Border W", 0, 10, ov.border_width)

        new_overlay = ImageOverlay(
            position=ov_pos, color=ov_color, opacity=ov_opacity,
            height_pct=ov_height, center_y_pct=ov_center_y, width_pct=ov_width,
            border_color=ov_border_color if ov_pos == "box" else None,
            border_width=ov_border_width if ov_pos == "box" else 0,
        )
    else:
        new_overlay = None

    # Available fonts
    FONTS = ["Montserrat.ttf", "BebasNeue.ttf", "Oswald.ttf", "PlayfairDisplay.ttf",
             "GreatVibes.ttf", "Sacramento.ttf", "DancingScript.ttf", "Lobster.ttf",
             "Pacifico.ttf", "Lora.ttf", "Merriweather.ttf", "Bangers.ttf",
             "PermanentMarker.ttf", "Righteous.ttf", "AbrilFatface.ttf", "NexaRust.otf"]

    # Default element for new additions
    DEFAULT_EL = {"title": (80, 70), "prefix": (52, 50), "tagline": (40, -140),
                  "accent": (36, 180), "watermark": (20, -50)}

    # Text elements - with enable toggle
    def edit_element(name: str, el: TextElement | None) -> TextElement | None:
        has_element = el is not None
        defaults = DEFAULT_EL.get(name, (40, 100))

        with st.expander(f"{name.title()}", expanded=has_element):
            enabled = st.checkbox("Enable", value=has_element, key=f"{name}_en")
            if not enabled:
                return None

            font = el.font_file if el else FONTS[0]
            font_file = st.selectbox("Font", FONTS, index=FONTS.index(font) if font in FONTS else 0, key=f"{name}_f")

            c1, c2, c3 = st.columns(3)
            y = c1.number_input("Y", -500, 1500, el.y_position if el else defaults[1], key=f"{name}_y")
            size = c2.number_input("Size", 10, 200, el.font_size if el else defaults[0], key=f"{name}_s")
            color = c3.color_picker("Color", to_hex(el.color) if el else "#FFFFFF", key=f"{name}_c")

            c4, c5, c6 = st.columns(3)
            outline = c4.number_input("Outline", 0, 10, el.outline_width if el else 3, key=f"{name}_o")
            align = c5.selectbox("Align", ["center", "left", "right"],
                                 index=["center", "left", "right"].index(el.alignment) if el else 0, key=f"{name}_a")
            angle = c6.number_input("Angle", -45, 45, el.angle if el else 0, key=f"{name}_ang")

        return TextElement(font_file=font_file, font_size=size, color=color,
                           y_position=y, outline_width=outline, alignment=align, angle=angle)

    new_elements = {k: edit_element(k, getattr(base_style, k))
                    for k in ["title", "prefix", "tagline", "accent", "watermark"]}

# Build modified style
modified_style = VisualStyle(
    name=base_style.name, description=base_style.description,
    overlay=new_overlay, **new_elements
)

with col2:
    st.subheader("Preview")
    try:
        preview = channel.render_content(source_img, text_data, modified_style, BRAND_TEXT)
        st.image(preview, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

    # Config export - compact format
    st.subheader("Config")

    def fmt_el(name: str, el: TextElement) -> str:
        parts = [f'font_file="{el.font_file}"', f"font_size={el.font_size}",
                 f'color="{el.color}"', f"y_position={el.y_position}"]
        if el.outline_width: parts.append(f"outline_width={el.outline_width}")
        if el.alignment != "center": parts.append(f'alignment="{el.alignment}"')
        if el.angle: parts.append(f"angle={el.angle}")
        return f"        {name}=TextElement({', '.join(parts)}),"

    def fmt_ov(ov: ImageOverlay) -> str:
        parts = [f'position="{ov.position}"', f'color="{ov.color}"',
                 f"opacity={ov.opacity}", f"height_pct={ov.height_pct}"]
        if ov.position in ["center", "box"]: parts.append(f"center_y_pct={ov.center_y_pct}")
        if ov.position == "box":
            parts.extend([f"width_pct={ov.width_pct}",
                         f'border_color="{ov.border_color}"', f"border_width={ov.border_width}"])
        return f"        overlay=ImageOverlay({', '.join(parts)}),"

    lines = [f'    "{modified_style.name}": VisualStyle(name="{modified_style.name}", description="...",']
    for k, el in new_elements.items():
        if el: lines.append(fmt_el(k, el))
    if new_overlay: lines.append(fmt_ov(new_overlay))
    lines.append("    ),")

    st.code("\n".join(lines), language="python")
