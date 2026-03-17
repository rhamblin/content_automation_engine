"""Pin-maker input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PinMakerRequest:
    """Defines what pin-maker accepts — validated from JSON or message payload."""

    input_folder: str  # folder containing keyword subfolders with images
    niche: str = "food"
    locale: str = "en"  # en | es | sw
    styles: list[str] | None = None  # None = use all available styles
