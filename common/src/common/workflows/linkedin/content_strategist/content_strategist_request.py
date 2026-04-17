from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContentStrategistConfig:
    """Configuration for the content strategist service."""

    persona_prompt: str
    grounding_dir: Path
    model: str
    project_endpoint: str
