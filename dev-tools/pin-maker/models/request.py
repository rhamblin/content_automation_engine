"""Pin-maker input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PinMakerRequest:
    """Defines what pin-maker accepts — validated from JSON or message payload."""

    input_folder: str  # required
    niche: str = "food"
    locale: str = "en"  # en | es | sw
    style: str | None = None  # None = cycle all styles
