"""Pin-uploader input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PinItem:
    """A single pin ready for upload — title/description already populated."""

    board_id: str
    image_b64: str
    content_type: str  # "image/jpeg"
    title: str
    description: str
    link: str | None = None
    alt_text: str | None = None


@dataclass(frozen=True)
class PinUploadRequest:
    """Batch of pins to upload. Secret-free — credentials injected via channel."""

    pins: list[PinItem]
