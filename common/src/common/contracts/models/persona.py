"""Persona - Voice/tone definition for niche-specific content generation."""

from dataclasses import dataclass


@dataclass
class Persona:
    """Defines the voice and tone for content generation within a niche."""

    name: str
    prompt: str  # Voice/tone instructions for LLM
