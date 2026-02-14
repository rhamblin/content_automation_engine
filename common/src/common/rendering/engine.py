"""Shared rendering engine — channel-agnostic image pipeline."""

from typing import Any

from PIL import Image, ImageDraw

from common.contracts.models import CanvasSpec, VisualStyle


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


def render_image(
    source: Image.Image,
    canvas: CanvasSpec,
    style: Any,
    text_data: dict,
    brand_text: str = "",
) -> Image.Image:
    """Render an image using the shared pipeline.

    Pipeline: crop/resize → overlays → RGBA → draw text → convert to canvas format.

    Args:
        source: Source PIL Image.
        canvas: CanvasSpec defining output dimensions and format.
        style: VisualStyle object (or None).
        text_data: Dict mapping element keys to text strings.
        brand_text: Brand watermark text.

    Returns:
        Final rendered PIL Image.
    """
    img = smart_crop_resize(source, canvas.width, canvas.height)

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
