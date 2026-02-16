"""Pin-maker output contract."""

from dataclasses import dataclass

from PIL import Image


@dataclass
class PinResult:
    """Result of rendering a single pin."""

    image: Image.Image | None
    keyword: str
    style_name: str
    title: str | None = None
    error: str | None = None
