"""Board-manager output contract."""

from dataclasses import dataclass, field


@dataclass
class BoardResult:
    """Result of a single board creation."""

    name: str
    board_id: str | None = None
    url: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class BoardManagerResponse:
    """Aggregate result of board creation batch."""

    results: list[BoardResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.ok)
