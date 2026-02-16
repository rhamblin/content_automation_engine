"""Publication-manager input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PublicationRequest:
    """Defines what publication-manager accepts."""

    command: str = "evaluate"  # evaluate
    days: int = 7
    limit: int | None = None
    min_impressions: int = 500
    high_ctr: float = 1.5
    low_ctr: float = 0.5
    high_save_rate: float = 2.0
    low_save_rate: float = 0.5
    actionable: bool = False
    output_json: bool = False
