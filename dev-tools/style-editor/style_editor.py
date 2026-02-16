"""Style Editor - Visual editor for pin styles. Pass ?channel=pinterest in URL."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.contracts.models import CanvasSpec, ImageOverlay, TextElement, VisualStyle
from common.contracts.models.rendering.image_overlay import STICKERS_DIR
from common.rendering import render_image

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

STYLES_ROOT = Path(__file__).parent.parent.parent / "config" / "tenants"

# Channel → default canvas (extensible)
CHANNEL_CANVAS = {
    "pinterest": CanvasSpec(width=1000, height=1500, format="RGB"),
}


def _load_styles(tenant: str, channel: str) -> dict[str, VisualStyle]:
    """Load all style JSONs from config/tenants/{tenant}/styles/{channel}/."""
    styles_dir = STYLES_ROOT / tenant / "styles" / channel
    if not styles_dir.exists():
        return {}
    styles: dict[str, VisualStyle] = {}
    for f in sorted(styles_dir.glob("*.json")):
        data = json.loads(f.read_text())
        styles[data["name"]] = VisualStyle.from_dict(data)
    return styles


SHAPES = ["rectangle", "ribbon", "pill", "sticker"]

def _list_stickers() -> list[str]:
    """List available sticker PNGs."""
    if not STICKERS_DIR.exists():
        return []
    return sorted(f.name for f in STICKERS_DIR.glob("*.png"))

# Convert named colors to hex for Streamlit color_picker
COLOR_MAP = {
    "white": "#FFFFFF", "black": "#000000", "red": "#FF0000",
    "green": "#00FF00", "blue": "#0000FF", "yellow": "#FFFF00",
    "orange": "#FFA500", "pink": "#FFC0CB", "gray": "#808080",
}

def to_hex(color: str) -> str:
    return COLOR_MAP.get(color.lower(), color) if not color.startswith("#") else color

def _kw(key: str, **default):
    """Return widget kwargs, omitting default value if session_state already owns the key."""
    if key in st.session_state:
        return {"key": key}
    return {"key": key, **default}

st.set_page_config(page_title="Style Editor", layout="wide")

# Wider sidebar for larger preview
st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 450px; max-width: 450px; }
</style>
""", unsafe_allow_html=True)

st.title("Style Editor")

channel_name = st.query_params.get("channel", "pinterest")
STYLES = _load_styles("dev-tenant", channel_name)
CANVAS = CHANNEL_CANVAS.get(channel_name, CanvasSpec(width=1000, height=1500, format="RGB"))

if not STYLES:
    st.error(f"No styles found for channel '{channel_name}' in config/tenants/dev-tenant/styles/")
    st.stop()

# Sidebar - Image upload and preview (sticky)
st.sidebar.header("Image")
uploaded = st.sidebar.file_uploader("Upload", type=["jpg", "jpeg", "png"])
source_img = Image.open(uploaded).convert("RGB") if uploaded else Image.new("RGB", (1000, 1500), "#8B4513")

st.sidebar.header("Style")
style_name = st.sidebar.selectbox("Base style", list(STYLES.keys()))

# Reset widget state when style changes
if "current_style" not in st.session_state:
    st.session_state.current_style = style_name
elif st.session_state.current_style != style_name:
    # Clear all widget keys to reset to new style defaults
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith(("ov_", "title_", "prefix_", "tagline_", "accent_", "watermark_", "num_overlay", "txt_"))]
    for k in keys_to_clear:
        del st.session_state[k]
    st.session_state.current_style = style_name
    st.rerun()

base_style = STYLES[style_name]

st.sidebar.header("Text")
text_data = {
    "title": st.sidebar.text_input("Title", "Delicious Recipe", key="txt_title"),
    "prefix": st.sidebar.text_input("Prefix", "Quick & Easy", key="txt_prefix"),
    "tagline": st.sidebar.text_input("Tagline", "Perfect for dinner", key="txt_tagline"),
    "accent": st.sidebar.text_input("Accent", "homemade", key="txt_accent"),
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
                for suffix in ("shape", "pos", "c", "op", "h", "y", "w", "bc", "bw",
                               "x", "ang", "notch", "cr", "stk", "fh", "fv"):
                    st.session_state.pop(f"ov_{idx}_{suffix}", None)
                return None

            shape = st.selectbox("Shape", SHAPES,
                                 **_kw(f"ov_{idx}_shape", index=SHAPES.index(defaults.shape) if defaults.shape in SHAPES else 0))

            # Sticker mode - simplified controls
            if shape == "sticker":
                stickers = _list_stickers()
                if not stickers:
                    st.warning("No stickers found. Add PNGs to resources/rendering/stickers/")
                    return None
                sticker_file = st.selectbox("Sticker", stickers,
                                            **_kw(f"ov_{idx}_stk", index=stickers.index(defaults.sticker_file) if defaults.sticker_file in stickers else 0))
                c1, c2 = st.columns(2)
                color = c1.color_picker("Color", **_kw(f"ov_{idx}_c", value=to_hex(defaults.color)))
                opacity = c2.slider("Opacity", 0.0, 1.0, **_kw(f"ov_{idx}_op", value=defaults.opacity))
                c3, c4 = st.columns(2)
                height = c3.slider("Height %", 0.05, 0.5, **_kw(f"ov_{idx}_h", value=defaults.height_pct))
                y_pos = c4.number_input("Y Position", -500, 1500, **_kw(f"ov_{idx}_y", value=defaults.y_position))
                c5, c6 = st.columns(2)
                x_pos = c5.number_input("X Position", -500, 500, **_kw(f"ov_{idx}_x", value=defaults.x_position))
                angle = c6.number_input("Angle", -180, 180, **_kw(f"ov_{idx}_ang", value=defaults.angle))
                c7, c8 = st.columns(2)
                flip_h = c7.checkbox("Flip H", **_kw(f"ov_{idx}_fh", value=defaults.flip_h))
                flip_v = c8.checkbox("Flip V", **_kw(f"ov_{idx}_fv", value=defaults.flip_v))
                return ImageOverlay(shape="sticker", sticker_file=sticker_file, color=color,
                                    opacity=opacity, height_pct=height, y_position=y_pos,
                                    x_position=x_pos, angle=angle, flip_h=flip_h, flip_v=flip_v)

            # Geometric shapes
            positions = ["top", "bottom", "center", "box", "full"]
            pos = st.selectbox("Position", positions,
                               **_kw(f"ov_{idx}_pos", index=positions.index(defaults.position)))
            c1, c2 = st.columns(2)
            color = c1.color_picker("Color", **_kw(f"ov_{idx}_c", value=to_hex(defaults.color)))
            opacity = c2.slider("Opacity", 0.0, 1.0, **_kw(f"ov_{idx}_op", value=defaults.opacity))
            c3, c4 = st.columns(2)
            height = c3.slider("Height %", 0.05, 0.5, **_kw(f"ov_{idx}_h", value=defaults.height_pct))
            y_pos = c4.number_input("Y Position", -500, 1500, **_kw(f"ov_{idx}_y", value=defaults.y_position))

            # Conditional widgets: show controls and clean up orphaned keys
            center_box_keys = [f"ov_{idx}_{s}" for s in ("bc", "bw", "x", "ang")]
            if pos in ["center", "box"]:
                c5, c6, c7, c8 = st.columns(4)
                border_color = c5.color_picker("Border Color", **_kw(f"ov_{idx}_bc", value=defaults.border_color))
                border_width = c6.slider("Border W", 0, 10, **_kw(f"ov_{idx}_bw", value=defaults.border_width))
                x_pos = c7.number_input("X Position", -500, 500, **_kw(f"ov_{idx}_x", value=defaults.x_position))
                angle = c8.number_input("Angle", -180, 180, **_kw(f"ov_{idx}_ang", value=defaults.angle))
            else:
                for k in center_box_keys:
                    st.session_state.pop(k, None)
                border_color, border_width, x_pos, angle = "#000000", 0, 0, 0

            if pos == "box":
                width = st.slider("Width %", 0.3, 1.0, **_kw(f"ov_{idx}_w", value=defaults.width_pct))
            else:
                st.session_state.pop(f"ov_{idx}_w", None)
                width = defaults.width_pct

            if shape == "ribbon":
                notch_pct = st.slider("Notch %", 0.01, 0.10, **_kw(f"ov_{idx}_notch", value=defaults.notch_pct))
            else:
                st.session_state.pop(f"ov_{idx}_notch", None)
                notch_pct = defaults.notch_pct

            if shape == "pill":
                corner_radius = st.number_input("Corner Radius", 1, 100, **_kw(f"ov_{idx}_cr", value=defaults.corner_radius))
            else:
                st.session_state.pop(f"ov_{idx}_cr", None)
                corner_radius = defaults.corner_radius

            return ImageOverlay(position=pos, color=color, opacity=opacity, height_pct=height,
                                y_position=y_pos, width_pct=width, border_color=border_color,
                                border_width=border_width, x_position=x_pos, angle=angle,
                                shape=shape, notch_pct=notch_pct, corner_radius=corner_radius)

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
                for suffix in ("f", "y", "s", "c", "o", "oc", "a", "ang"):
                    st.session_state.pop(f"{name}_{suffix}", None)
                return None

            font = el.font_file if el else FONTS[0]
            font_file = st.selectbox("Font", FONTS, **_kw(f"{name}_f", index=FONTS.index(font) if font in FONTS else 0))

            c1, c2, c3 = st.columns(3)
            y = c1.number_input("Y", -500, 1500, **_kw(f"{name}_y", value=el.y_position if el else defaults[1]))
            size = c2.number_input("Size", 10, 200, **_kw(f"{name}_s", value=el.font_size if el else defaults[0]))
            color = c3.color_picker("Color", **_kw(f"{name}_c", value=to_hex(el.color) if el else "#FFFFFF"))

            c4, c5 = st.columns(2)
            outline = c4.number_input("Outline W", 0, 10, **_kw(f"{name}_o", value=el.outline_width if el else 3))
            outline_color = c5.color_picker("Outline Color", **_kw(f"{name}_oc", value=to_hex(el.outline_color) if el else "#000000"))

            c6, c7 = st.columns(2)
            aligns = ["center", "left", "right"]
            align = c6.selectbox("Align", aligns,
                                 **_kw(f"{name}_a", index=aligns.index(el.alignment) if el else 0))
            angle = c7.number_input("Angle", -180, 180, **_kw(f"{name}_ang", value=el.angle if el else 0))

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
    st.subheader("Config (JSON)")

    def _el_to_dict(el: TextElement) -> dict:
        """Convert TextElement to JSON-serializable dict, omitting defaults."""
        d = asdict(el)
        # Remove defaults to keep config compact
        defaults = {"outline_width": 0, "outline_color": "#000000", "alignment": "center",
                    "max_width_pct": 0.85, "max_lines": 2, "angle": 0}
        return {k: v for k, v in d.items() if k not in defaults or v != defaults[k]}

    def _ov_to_dict(ov: ImageOverlay) -> dict:
        """Convert ImageOverlay to JSON-serializable dict, omitting defaults."""
        d = asdict(ov)
        defaults = {"position": "top", "color": "#000000", "opacity": 0.3, "height_pct": 0.35,
                    "y_position": 750, "width_pct": 0.7, "border_color": "#000000", "border_width": 0,
                    "x_position": 0, "angle": 0, "shape": "rectangle", "notch_pct": 0.03,
                    "corner_radius": 20, "sticker_file": None, "flip_h": False, "flip_v": False}
        return {k: v for k, v in d.items() if k not in defaults or v != defaults[k]}

    spec: dict = {}
    for k, el in new_elements.items():
        if el:
            spec[k] = _el_to_dict(el)
    if new_overlays:
        spec["overlays"] = [_ov_to_dict(ov) for ov in new_overlays]

    config = {
        "name": modified_style.name,
        "channel": channel_name,
        "description": modified_style.description,
        "spec": spec,
    }

    st.code(json.dumps(config, indent=2), language="json")

# Preview in sidebar (naturally sticky)
st.sidebar.header("Preview")
try:
    _settings = load_dev_settings()
    preview = render_image(source_img, CANVAS, modified_style, text_data, _settings.brand_text)
    st.sidebar.image(preview, width=420)
except Exception as e:
    st.sidebar.error(f"Error: {e}")
