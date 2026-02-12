"""Niche-to-persona mapping for content generation."""

from common.contracts.models import Persona

PERSONAS: dict[str, Persona] = {
    "food": Persona(
        name="home_cook",
        prompt="""You are a warm, friendly home cook with a housewife persona.
Write in an inviting, comforting, family-oriented tone.
Sound like you're chatting with friends in your kitchen.
Use engaging, family-friendly language that evokes comfort and togetherness.""",
    ),
}


def get_persona(niche: str) -> Persona | None:
    """Get persona for a niche, or None if not defined."""
    return PERSONAS.get(niche)
