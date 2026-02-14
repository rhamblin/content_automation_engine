import json

from openai import APIError, AzureOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from common.app_logger import AppLogger

from common.contracts.interfaces import IDistributionChannel, ILLMProvider

LOCALE_INSTRUCTIONS = {
    "en": "",
    "es": (
        "IMPORTANT: You MUST write ALL content in Spanish (español). "
        "Every field — title, tagline, prefix, accent, description — must be in Spanish. "
        "Do NOT leave any field in English. Ignore English examples; translate the intent."
    ),
    "sw": (
        "IMPORTANT: You MUST write ALL content in Swahili (Kiswahili). "
        "Every field — title, tagline, prefix, accent, description — must be in Swahili. "
        "Do NOT leave any field in English. Ignore English examples; translate the intent."
    ),
    "pt": (
        "IMPORTANT: You MUST write ALL content in Portuguese (português). "
        "Every field — title, tagline, prefix, accent, description — must be in Portuguese. "
        "Do NOT leave any field in English. Ignore English examples; translate the intent."
    ),
}


class AzureFoundryLLMProvider(ILLMProvider):
    """Azure Foundry LLM provider.

    Raises:
        ConnectionError: When Azure OpenAI API is unreachable.
        ValueError: When response is empty or invalid JSON.
    """

    @property
    def provider_name(self) -> str:
        return "azure_foundry"

    STYLE_PROMPT_TEMPLATE = """
Generate text for the "{style_name}" style.
Style description: {style_description}

Generate ONLY these fields:
{{
{fields}
}}

Guidelines:
- Include the main keyword naturally
- NEVER use emoji or unicode symbols - plain text only
- Text is rendered on images at large sizes, keep it short and punchy
{field_guidelines}

Return ONLY valid JSON with the exact fields shown above.
"""

    def __init__(self, azure_open_ai_client: AzureOpenAI):
        self.client = azure_open_ai_client
        self.logger = AppLogger(__name__)

    def _build_prompt(
        self,
        channel: IDistributionChannel,
        persona=None,
        style=None,
        locale: str = "en",
    ) -> str:
        """Build system prompt: channel (platform) + persona (voice) + style (fields) + locale."""
        locale_instruction = LOCALE_INSTRUCTIONS.get(locale, LOCALE_INSTRUCTIONS["en"])

        prompt = channel.system_prompt

        if locale_instruction:
            prompt = f"{locale_instruction}\n\n{prompt}"

        if persona:
            prompt = f"{prompt}\n\n{persona.prompt}"

        if style:
            field_lines, guidelines = style.prompt_schema()
            style_section = self.STYLE_PROMPT_TEMPLATE.format(
                style_name=style.name,
                style_description=style.description,
                fields=",\n  ".join(field_lines),
                field_guidelines=(
                    "\n".join(f"- {g}" for g in guidelines) if guidelines else ""
                ),
            )
            prompt = f"{prompt}\n\n{style_section}"

        return prompt

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ValueError),
        reraise=True,
    )
    def _call_llm(
        self,
        niche: str,
        keyword: str,
        channel: IDistributionChannel,
        persona=None,
        style=None,
        locale: str = "en",
        image_url: str = "",
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self._build_prompt(channel, persona, style, locale),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Niche: {niche}\n"
                            f"Primary keyword: {keyword}\n"
                            f"Image URL: {image_url}\n"
                        ),
                    },
                ],
                max_completion_tokens=50000,
                model="gpt-5-nano",
            )
        except APIError as e:
            raise ConnectionError(f"Azure OpenAI API error: {e}") from e

        if not response.choices or response.choices[0].message.content is None:
            self.logger.warning(
                f"Empty response from Azure OpenAI, "
                f"finish_reason={getattr(response.choices[0], 'finish_reason', 'N/A') if response.choices else 'no choices'}"
            )
            raise ValueError("Azure OpenAI returned empty content")

        return response.choices[0].message.content

    def generate(
        self,
        niche: str,
        keyword: str,
        channel: IDistributionChannel,
        persona=None,
        style=None,
        locale: str = "en",
        image_url: str = "",
    ) -> dict:
        """Generate content using Azure OpenAI.

        Raises:
            ConnectionError: When Azure OpenAI API is unreachable.
            ValueError: When response is empty or invalid JSON.
        """
        raw_result = self._call_llm(niche, keyword, channel, persona, style, locale, image_url)
        try:
            json_equiv = json.loads(raw_result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Azure OpenAI returned invalid JSON: {e}") from e

        return json_equiv
