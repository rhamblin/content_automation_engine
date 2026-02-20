"""Pin-maker input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PinMakerRequest:
    """Defines what pin-maker accepts — validated from JSON or message payload."""

    niche: str = "food"
    locale: str = "en"  # en | es | sw
    styles: list[str] | None = None  # None = use all available styles
    keywords: list[dict] | None = None  # [{"keyword": "...", "image_path": "..."}]
    input_folder: str | None = None  # folder containing image files

    def __post_init__(self):
        has_keywords = self.keywords is not None
        has_folder = self.input_folder is not None
        if has_keywords and has_folder:
            raise ValueError("Provide either 'keywords' or 'input_folder', not both")
        if not has_keywords and not has_folder:
            raise ValueError("Provide either 'keywords' or 'input_folder'")
