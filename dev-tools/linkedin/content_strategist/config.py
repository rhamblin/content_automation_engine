"""Config loader — reads JSON data file, resolves tenant prompt and grounding paths."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from common.workflows.linkedin.content_strategist import ContentStrategistConfig

logger = logging.getLogger(__name__)

CONFIG_ROOT = Path(__file__).parent.parent.parent.parent / "config" / "tenants"
ENV_FILE = Path(__file__).parent.parent.parent / ".env"


@dataclass(frozen=True)
class StrategistToolConfig:
    """Validated config from data file + tenant LinkedIn config."""

    service_config: ContentStrategistConfig
    tenant: str


def load_config(path: Path) -> StrategistToolConfig:
    """Load a JSON data file, resolve tenant config, return validated config."""
    load_dotenv(ENV_FILE)

    raw = json.loads(path.read_text())

    if "tenant" not in raw:
        raise ValueError("data file missing required field: tenant")

    tenant = raw["tenant"]
    model = raw.get("model", "gpt-4o")

    # --- project endpoint ---
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
    if not project_endpoint:
        raise ValueError(
            "AZURE_AI_PROJECT_ENDPOINT not set in environment or .env file. "
            "Set it to your Azure AI Foundry project endpoint."
        )

    # --- resolve tenant LinkedIn config ---
    linkedin_dir = CONFIG_ROOT / tenant / "linkedin"
    if not linkedin_dir.exists():
        raise ValueError(f"LinkedIn config directory not found: {linkedin_dir}")

    # --- persona prompt ---
    prompt_path = linkedin_dir / "prompts" / "strategist.txt"
    if not prompt_path.exists():
        raise ValueError(f"Persona prompt not found: {prompt_path}")

    persona_prompt = prompt_path.read_text().strip()
    if not persona_prompt:
        raise ValueError(f"Persona prompt is empty: {prompt_path}")

    # --- grounding directory ---
    grounding_dir = linkedin_dir / "grounding"
    if not grounding_dir.exists():
        logger.warning(
            "Grounding directory does not exist: %s — agent will run without RAG",
            grounding_dir,
        )

    service_config = ContentStrategistConfig(
        persona_prompt=persona_prompt,
        grounding_dir=grounding_dir,
        model=model,
        project_endpoint=project_endpoint,
    )

    return StrategistToolConfig(service_config=service_config, tenant=tenant)
