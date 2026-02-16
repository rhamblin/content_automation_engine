"""Title-generator output contract."""

from dataclasses import dataclass, field


@dataclass
class TitleOption:
    """A single generated title/description pair."""

    title: str
    description: str
    reasoning: str = ""
    alt_text: str = ""


@dataclass
class TitleGenResult:
    """Result of a title generation run."""

    options: list[TitleOption] = field(default_factory=list)
    error: str | None = None
