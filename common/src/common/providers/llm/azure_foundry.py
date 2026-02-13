import json

from openai import APIError, AzureOpenAI

from common.contracts.interfaces import IDistributionChannel, ILLMProvider

LOCALE_INSTRUCTIONS = {
    "en": "Respond in English.",
    "es": "Responde en español.",
    "sw": "Jibu kwa Kiswahili.",
    "pt": "Responda em português.",
}


class AzureFoundryLLMProvider(ILLMProvider):
    """Azure Foundry LLM provider.

    Raises:
        ConnectionError: When Azure OpenAI API is unreachable.
        ValueError: When response is empty or invalid JSON.
    """

    PROVIDER_NAME = "azure_foundry"

    STYLE_PROMPT_TEMPLATE = """
Generate text for the "{style_name}" style.
Style description: {style_description}

Generate ONLY these fields:
{{
{fields}
}}

Guidelines:
- Include the main keyword naturally
{field_guidelines}

Return ONLY valid JSON with the exact fields shown above.
"""

    def __init__(self, azure_open_ai_client: AzureOpenAI):
        self.client = azure_open_ai_client

    def _build_prompt(
        self,
        channel: IDistributionChannel,
        persona=None,
        style=None,
        locale: str = "en",
    ) -> str:
        """Build system prompt: channel (platform) + persona (voice) + style (fields) + locale."""
        prompt = channel.system_prompt

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

        locale_instruction = LOCALE_INSTRUCTIONS.get(locale, LOCALE_INSTRUCTIONS["en"])
        prompt = f"{prompt}\n\n{locale_instruction}"

        return prompt

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

        if not response.choices:
            raise ValueError("Azure OpenAI returned no choices")

        raw_result = response.choices[0].message.content
        if raw_result is None:
            raise ValueError("Azure OpenAI returned empty content")
        try:
            json_equiv = json.loads(raw_result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Azure OpenAI returned invalid JSON: {e}") from e

        return json_equiv
