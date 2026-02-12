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

# Wider sidebar for larger preview
st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 450px; max-width: 450px; }
</style>
""", unsafe_allow_html=True)

st.title("Style Explorer")

channel = PinterestChannel()

# Sidebar - Image upload and preview (sticky)
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
    # Overlays (multiple)
    st.subheader("Overlays")

    def edit_overlay(idx: int, ov: ImageOverlay | None) -> ImageOverlay | None:
        """Edit a single overlay, returns None if disabled."""
        defaults = ov or ImageOverlay()
        with st.expander(f"Overlay {idx + 1}" + (f" ({ov.position})" if ov else ""), expanded=ov is not None):
            enabled = st.checkbox("Enable", value=ov is not None, key=f"ov_{idx}_en")
            if not enabled:
                return None

            pos = st.selectbox("Position", ["top", "bottom", "center", "box", "full"],
                               index=["top", "bottom", "center", "box", "full"].index(defaults.position), key=f"ov_{idx}_pos")
            c1, c2 = st.columns(2)
            color = c1.color_picker("Color", to_hex(defaults.color), key=f"ov_{idx}_c")
            opacity = c2.slider("Opacity", 0.0, 1.0, defaults.opacity, key=f"ov_{idx}_op")
            c3, c4 = st.columns(2)
            height = c3.slider("Height %", 0.05, 0.5, defaults.height_pct, key=f"ov_{idx}_h")
            y_pos = c4.number_input("Y Position", -500, 1500, defaults.y_position, key=f"ov_{idx}_y")

            width, border_color, border_width, angle = defaults.width_pct, "#000000", 0, 0
            if pos in ["center", "box"]:
                c5, c6, c7 = st.columns(3)
                border_color = c5.color_picker("Border Color", defaults.border_color, key=f"ov_{idx}_bc")
                border_width = c6.slider("Border W", 0, 10, defaults.border_width, key=f"ov_{idx}_bw")
                angle = c7.number_input("Angle", -180, 180, defaults.angle, key=f"ov_{idx}_ang")
            if pos == "box":
                width = st.slider("Width %", 0.3, 1.0, defaults.width_pct, key=f"ov_{idx}_w")

            return ImageOverlay(position=pos, color=color, opacity=opacity, height_pct=height,
                                y_position=y_pos, width_pct=width, border_color=border_color,
                                border_width=border_width, angle=angle)

    # Dynamic overlay slots
    base_overlays = base_style.overlays if base_style.overlays else []
    if "num_overlay_slots" not in st.session_state:
        st.session_state.num_overlay_slots = max(1, len(base_overlays))

    new_overlays = []
    for i in range(st.session_state.num_overlay_slots):
        ov = base_overlays[i] if i < len(base_overlays) else None
        result = edit_overlay(i, ov)
        if result:
            new_overlays.append(result)

    if st.button("+ Add Overlay"):
        st.session_state.num_overlay_slots += 1
        st.rerun()

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

            c4, c5 = st.columns(2)
            outline = c4.number_input("Outline W", 0, 10, el.outline_width if el else 3, key=f"{name}_o")
            outline_color = c5.color_picker("Outline Color", to_hex(el.outline_color) if el else "#000000", key=f"{name}_oc")

            c6, c7 = st.columns(2)
            align = c6.selectbox("Align", ["center", "left", "right"],
                                 index=["center", "left", "right"].index(el.alignment) if el else 0, key=f"{name}_a")
            angle = c7.number_input("Angle", -180, 180, el.angle if el else 0, key=f"{name}_ang")

        return TextElement(font_file=font_file, font_size=size, color=color,
                           y_position=y, outline_width=outline, outline_color=outline_color,
                           alignment=align, angle=angle)

    new_elements = {k: edit_element(k, getattr(base_style, k))
                    for k in ["title", "prefix", "tagline", "accent", "watermark"]}

# Build modified style
modified_style = VisualStyle(
    name=base_style.name, description=base_style.description,
    overlays=new_overlays, **new_elements
)

with col2:
    st.subheader("Config")

    def fmt_el(name: str, el: TextElement) -> str:
        parts = [f'font_file="{el.font_file}"', f"font_size={el.font_size}",
                 f'color="{el.color}"', f"y_position={el.y_position}"]
        if el.outline_width:
            parts.append(f"outline_width={el.outline_width}")
        if el.outline_color != "#000000":
            parts.append(f'outline_color="{el.outline_color}"')
        if el.alignment != "center":
            parts.append(f'alignment="{el.alignment}"')
        if el.angle:
            parts.append(f"angle={el.angle}")
        return f"        {name}=TextElement({', '.join(parts)}),"

    def fmt_ov(ov: ImageOverlay) -> str:
        parts = [f'position="{ov.position}"', f'color="{ov.color}"',
                 f"opacity={ov.opacity}", f"height_pct={ov.height_pct}"]
        if ov.position in ["center", "box"]:
            parts.append(f"y_position={ov.y_position}")
            if ov.border_width:
                parts.extend([f'border_color="{ov.border_color}"', f"border_width={ov.border_width}"])
            if ov.angle:
                parts.append(f"angle={ov.angle}")
        if ov.position == "box":
            parts.append(f"width_pct={ov.width_pct}")
        return f"ImageOverlay({', '.join(parts)})"

    lines = [f'    "{modified_style.name}": VisualStyle(name="{modified_style.name}", description="...",']
    for k, el in new_elements.items():
        if el:
            lines.append(fmt_el(k, el))
    if new_overlays:
        ov_strs = [fmt_ov(ov) for ov in new_overlays]
        lines.append(f"        overlays=[{', '.join(ov_strs)}],")
    lines.append("    ),")

    st.code("\n".join(lines), language="python")

# Preview in sidebar (naturally sticky)
st.sidebar.header("Preview")
try:
    preview = channel.render_content(source_img, text_data, modified_style, BRAND_TEXT)
    st.sidebar.image(preview, width=420)
except Exception as e:
    st.sidebar.error(f"Error: {e}")
