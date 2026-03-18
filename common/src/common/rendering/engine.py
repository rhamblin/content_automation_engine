"""Shared rendering engine — channel-agnostic image pipeline."""

from typing import Any

from PIL import Image, ImageDraw

from common.contracts.models import CanvasSpec, Layout, VisualStyle


def scale_to_fit(
    img: Image.Image, target_w: int, target_h: int, bg_color: str = "#000000"
) -> Image.Image:
    """Scale image to fit within target dimensions, letterboxing with bg_color."""
    img = img.copy()
    img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), bg_color)
    x = (target_w - img.width) // 2
    y = (target_h - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def smart_crop_resize(
    img: Image.Image, target_w: int, target_h: int
) -> Image.Image:
    """Resize and crop image to target dimensions."""
    orig_w, orig_h = img.size
    target_ratio = target_w / target_h
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
    else:
        new_h = int(orig_w / target_ratio)
        top = (orig_h - new_h) // 3
        img = img.crop((0, top, orig_w, top + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def _crop_with_focus(
    img: Image.Image, target_w: int, target_h: int, focus: str = "center"
) -> Image.Image:
    """Resize and crop with vertical focus control."""
    orig_w, orig_h = img.size
    target_ratio = target_w / target_h
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
    else:
        new_h = int(orig_w / target_ratio)
        if focus == "top":
            top = 0
        elif focus == "bottom":
            top = orig_h - new_h
        else:
            top = (orig_h - new_h) // 2
        img = img.crop((0, top, orig_w, top + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def compose_canvas(
    source: Image.Image, canvas: CanvasSpec, layout: Layout, product: bool = False
) -> Image.Image:
    """Build the background canvas from source image according to layout type."""
    w, h = canvas.width, canvas.height

    if layout.type == "single":
        if product:
            return scale_to_fit(source, w, h, layout.color)
        return smart_crop_resize(source, w, h)

    if layout.type == "split_duplicate":
        top_h = int(h * layout.split_pct)
        bot_h = h - top_h - layout.gap
        if product:
            top_img = scale_to_fit(source, w, top_h, layout.color)
            bot_img = scale_to_fit(source, w, bot_h, layout.color)
        else:
            top_img = _crop_with_focus(source, w, top_h, layout.crop_focus_top)
            bot_img = _crop_with_focus(source, w, bot_h, layout.crop_focus_bottom)
        composed = Image.new("RGB", (w, h), layout.color)
        composed.paste(top_img, (0, 0))
        composed.paste(bot_img, (0, top_h + layout.gap))
        return composed

    if layout.type == "split_horizontal":
        left_w = int(w * layout.split_pct)
        right_w = w - left_w - layout.gap
        if product:
            left_img = scale_to_fit(source, left_w, h, layout.color)
            right_img = scale_to_fit(source, right_w, h, layout.color)
        else:
            left_img = _crop_with_focus(source, left_w, h, layout.crop_focus_top)
            right_img = _crop_with_focus(source, right_w, h, layout.crop_focus_bottom)
        composed = Image.new("RGB", (w, h), layout.color)
        composed.paste(left_img, (0, 0))
        composed.paste(right_img, (left_w + layout.gap, 0))
        return composed

    if layout.type == "grid_2x2":
        cell_w = (w - layout.gap) // 2
        cell_h = (h - layout.gap) // 2
        if product:
            cell = scale_to_fit(source, cell_w, cell_h, layout.color)
        else:
            cell = smart_crop_resize(source, cell_w, cell_h)
        composed = Image.new("RGB", (w, h), layout.color)
        composed.paste(cell, (0, 0))
        composed.paste(cell, (cell_w + layout.gap, 0))
        composed.paste(cell, (0, cell_h + layout.gap))
        composed.paste(cell, (cell_w + layout.gap, cell_h + layout.gap))
        return composed

    if layout.type == "image_over_color":
        img_h = int(h * layout.split_pct)
        if product:
            top_img = scale_to_fit(source, w, img_h, layout.color)
        else:
            top_img = _crop_with_focus(source, w, img_h, layout.crop_focus_top)
        composed = Image.new("RGB", (w, h), layout.color)
        composed.paste(top_img, (0, 0))
        return composed

    if layout.type == "color_over_image":
        img_h = int(h * (1.0 - layout.split_pct))
        if product:
            bot_img = scale_to_fit(source, w, img_h, layout.color)
        else:
            bot_img = _crop_with_focus(source, w, img_h, layout.crop_focus_bottom)
        composed = Image.new("RGB", (w, h), layout.color)
        composed.paste(bot_img, (0, h - img_h))
        return composed

    # Fallback to single
    if product:
        return scale_to_fit(source, w, h, layout.color)
    return smart_crop_resize(source, w, h)


def render_image(
    source: Image.Image,
    canvas: CanvasSpec,
    style: Any,
    text_data: dict,
    brand_text: str = "",
    product: bool = False,
) -> Image.Image:
    """Render an image using the shared pipeline.

    Pipeline: compose canvas → overlays → RGBA → draw text → convert to canvas format.

    Args:
        source: Source PIL Image.
        canvas: CanvasSpec defining output dimensions and format.
        style: VisualStyle object (or None).
        text_data: Dict mapping element keys to text strings.
        brand_text: Brand watermark text.
        product: If True, scale-to-fit instead of crop/zoom.

    Returns:
        Final rendered PIL Image.
    """
    layout = style.layout if style and hasattr(style, "layout") else Layout()
    img = compose_canvas(source, canvas, layout, product=product)

    if style and style.overlays:
        for overlay in style.overlays:
            img = overlay.apply(img)

    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    if style:
        for key, element in style.elements():
            text = brand_text if key == "watermark" else text_data.get(key)
            if text:
                result = element.draw(draw, text, img.width, img.height, base_img=img)
                if result is not None:
                    img = result
                    draw = ImageDraw.Draw(img)

    return img.convert(canvas.format)
