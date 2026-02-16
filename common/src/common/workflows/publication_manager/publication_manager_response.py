"""Publication-manager output contract."""

from dataclasses import dataclass, field


@dataclass
class PinEvaluation:
    """Result of evaluating a single pin."""

    pin_id: str
    title: str
    link: str
    action: str
    reason: str
    metrics: dict = field(default_factory=dict)
