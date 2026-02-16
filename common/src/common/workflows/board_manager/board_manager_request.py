"""Board-manager input contract."""

from dataclasses import dataclass

VALID_PRIVACY = {"PUBLIC", "SECRET"}


@dataclass(frozen=True)
class BoardItem:
    """A single board to create."""

    name: str
    privacy: str = "PUBLIC"  # PUBLIC | SECRET
