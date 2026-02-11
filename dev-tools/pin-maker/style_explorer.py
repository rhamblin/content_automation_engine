"""Style Explorer - Visual editor for Pinterest pin styles."""

import sys
from dataclasses import asdict, fields
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.contracts.models import ImageOverlay, TextElement, VisualStyle
from common.providers.distribution_channel.pinterest import PinterestChannel

from styles import BRAND_TEXT, STYLES

# Page config
st.set_page_config(page_title="Style Explorer", layout="wide")
st.title("Pinterest Style Explorer")

# Initialize channel
channel = PinterestChannel()

# Sidebar - Image upload
st.sidebar.header("Sample Image")
uploaded = st.sidebar.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

if uploaded:
    source_img = Image.open(uploaded).convert("RGB")
else:
    st.sidebar.info("Using placeholder image")
    # Create a simple gradient placeholder
    source_img = Image.new("RGB", (1000, 1500), "#8B4513")

# Style selector
st.sidebar.header("Style")
style_name = st.sidebar.selectbox("Select style", list(STYLES.keys()))
base_style = STYLES[style_name]

# Sample text
st.sidebar.header("Sample Text")
sample_title = st.sidebar.text_input("Title", "Delicious Recipe Title")
sample_prefix = st.sidebar.text_input("Prefix", "Quick & Easy")
sample_tagline = st.sidebar.text_input("Tagline", "Perfect for any occasion")
sample_accent = st.sidebar.text_input("Accent", "homemade goodness")

text_data = {
    "title": sample_title,
    "prefix": sample_prefix,
    "tagline": sample_tagline,
    "accent": sample_accent,
}

# Main area - two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Adjust Style")

    # Overlay settings
    st.subheader("Overlay")
    overlay = base_style.overlay
    if overlay:
        ov_position = st.selectbox("Position", ["top", "bottom", "center", "box", "full"],
                                   index=["top", "bottom", "center", "box", "full"].index(overlay.position))
        ov_color = st.color_picker("Color", overlay.color if overlay.color != "black" else "#000000")
        ov_opacity = st.slider("Opacity", 0.0, 1.0, overlay.opacity)
        ov_height_pct = st.slider("Height %", 0.05, 0.5, overlay.height_pct)
        ov_center_y_pct = st.slider("Center Y %", 0.0, 1.0, overlay.center_y_pct)

        # Box-specific settings
        if ov_position == "box":
            ov_width_pct = st.slider("Width %", 0.3, 1.0, overlay.width_pct)
            ov_border_color = st.color_picker("Border Color", overlay.border_color or "#333333")
            ov_border_width = st.slider("Border Width", 0, 10, overlay.border_width)
        else:
            ov_width_pct = overlay.width_pct
            ov_border_color = overlay.border_color
            ov_border_width = overlay.border_width

        new_overlay = ImageOverlay(
            position=ov_position,
            color=ov_color,
            opacity=ov_opacity,
            height_pct=ov_height_pct,
            center_y_pct=ov_center_y_pct,
            width_pct=ov_width_pct,
            border_color=ov_border_color if ov_position == "box" else None,
            border_width=ov_border_width if ov_position == "box" else 0,
        )
    else:
        new_overlay = None
        st.info("No overlay defined")

    # Text elements
    def edit_text_element(name: str, element: TextElement | None) -> TextElement | None:
        if element is None:
            return None

        st.subheader(f"{name.title()}")
        col_a, col_b = st.columns(2)
        with col_a:
            y_pos = st.number_input(f"{name} Y position", -500, 1500, element.y_position, key=f"{name}_y")
            font_size = st.number_input(f"{name} Font size", 10, 200, element.font_size, key=f"{name}_fs")
            outline = st.number_input(f"{name} Outline", 0, 10, element.outline_width, key=f"{name}_ol")
        with col_b:
            color = st.color_picker(f"{name} Color", element.color, key=f"{name}_color")
            alignment = st.selectbox(f"{name} Alignment", ["center", "left", "right"],
                                     index=["center", "left", "right"].index(element.alignment), key=f"{name}_align")
            angle = st.number_input(f"{name} Angle", -45, 45, element.angle, key=f"{name}_angle")

        return TextElement(
            font_file=element.font_file,
            font_size=font_size,
            color=color,
            y_position=y_pos,
            outline_width=outline,
            outline_color=element.outline_color,
            alignment=alignment,
            angle=angle,
        )

    new_title = edit_text_element("title", base_style.title)
    new_prefix = edit_text_element("prefix", base_style.prefix)
    new_tagline = edit_text_element("tagline", base_style.tagline)
    new_accent = edit_text_element("accent", base_style.accent)
    new_watermark = edit_text_element("watermark", base_style.watermark)

# Create modified style
modified_style = VisualStyle(
    name=base_style.name,
    description=base_style.description,
    title=new_title,
    prefix=new_prefix,
    tagline=new_tagline,
    accent=new_accent,
    watermark=new_watermark,
    overlay=new_overlay,
)

with col2:
    st.header("Preview")

    # Render preview
    try:
        preview = channel.render_content(
            source=source_img,
            text_data=text_data,
            style=modified_style,
            brand_text=BRAND_TEXT,
        )
        st.image(preview, use_container_width=True)
    except Exception as e:
        st.error(f"Render error: {e}")

    # Export config
    st.header("Config Export")

    def format_text_element(name: str, el: TextElement | None) -> str:
        if el is None:
            return ""
        return f'''        {name}=TextElement(
            font_file="{el.font_file}",
            font_size={el.font_size},
            color="{el.color}",
            y_position={el.y_position},
            outline_width={el.outline_width},
            alignment="{el.alignment}",
            angle={el.angle},
        ),'''

    def format_overlay(ov: ImageOverlay | None) -> str:
        if ov is None:
            return ""
        if ov.position == "box":
            return f'''        overlay=ImageOverlay(
            position="{ov.position}",
            color="{ov.color}",
            opacity={ov.opacity},
            height_pct={ov.height_pct},
            center_y_pct={ov.center_y_pct},
            width_pct={ov.width_pct},
            border_color="{ov.border_color}",
            border_width={ov.border_width},
        ),'''
        else:
            return f'''        overlay=ImageOverlay(
            position="{ov.position}",
            color="{ov.color}",
            opacity={ov.opacity},
            height_pct={ov.height_pct},
            center_y_pct={ov.center_y_pct},
        ),'''

    config_parts = [f'''    "{modified_style.name}": VisualStyle(
        name="{modified_style.name}",
        description="{modified_style.description}",''']

    if new_title:
        config_parts.append(format_text_element("title", new_title))
    if new_prefix:
        config_parts.append(format_text_element("prefix", new_prefix))
    if new_tagline:
        config_parts.append(format_text_element("tagline", new_tagline))
    if new_accent:
        config_parts.append(format_text_element("accent", new_accent))
    if new_watermark:
        config_parts.append(format_text_element("watermark", new_watermark))
    if new_overlay:
        config_parts.append(format_overlay(new_overlay))

    config_parts.append("    ),")

    config_code = "\n".join(config_parts)
    st.code(config_code, language="python")

    # Copy button hint
    st.caption("Copy the config above and paste into styles.py")
