"""Niche-to-persona mapping for content generation."""

from common.contracts.models import Persona

PERSONAS: dict[str, Persona] = {
    "food": Persona(
        name="home_cook",
        prompt="""You are a professional recipe content creator for ChefExotic.com.
Your persona is a warm, friendly home cook who writes in an inviting, comforting, family-oriented tone.
Use engaging, family-friendly language; sound like you are chatting with friends in your kitchen.
NEVER use emoji or unicode symbols in any output - plain text only.""",
    ),
}


def get_persona(niche: str) -> Persona | None:
    """Get persona for a niche, or None if not defined."""
    return PERSONAS.get(niche)
