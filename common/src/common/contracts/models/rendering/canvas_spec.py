"""Canvas specification for rendering channels."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CanvasSpec:
    """Defines canvas dimensions and format for a distribution channel."""

    width: int
    height: int
    format: str = "RGB"
