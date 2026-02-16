"""Pin-uploader output contract."""

from dataclasses import dataclass, field


@dataclass
class PinResult:
    """Result of a single pin upload."""

    board_id: str
    title: str
    pin_id: str | None = None
    url: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class PinUploadResponse:
    """Aggregate result of a pin upload batch."""

    results: list[PinResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.ok)
