from dataclasses import dataclass


@dataclass(frozen=True)
class ChatResponse:
    """A single response from the content strategist agent."""

    message: str
    annotations: list[str]
