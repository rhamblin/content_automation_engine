import json

from openai import APIError, AzureOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

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
        copy_style_prompt: str | None = None,
        persona_prompt: str | None = None,
        audience_prompt: str | None = None,
    ) -> str:
        """Build system prompt: channel (platform) + persona (voice) + style (fields) + locale + copy style + audience."""
        locale_instruction = LOCALE_INSTRUCTIONS.get(locale, LOCALE_INSTRUCTIONS["en"])

        prompt = channel.system_prompt

        if locale_instruction:
            prompt = f"{locale_instruction}\n\n{prompt}"

        if persona_prompt:
            prompt = f"{prompt}\n\n{persona_prompt}"
        elif persona:
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

        if copy_style_prompt:
            prompt = f"{prompt}\n\n{copy_style_prompt}"

        if audience_prompt:
            prompt = f"{prompt}\n\n{audience_prompt}"

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
        blog_url: str = "",
        copy_style_prompt: str | None = None,
        persona_prompt: str | None = None,
        audience_prompt: str | None = None,
        image_base64: str | None = None,
    ) -> str:
        user_text = f"Niche: {niche}\n" f"Primary keyword: {keyword}\n"
        if blog_url:
            user_text += f"Blog URL: {blog_url}\n"

        if image_base64:
            user_content = [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
            ]
        else:
            user_content = user_text

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self._build_prompt(
                            channel,
                            persona,
                            style,
                            locale,
                            copy_style_prompt,
                            persona_prompt,
                            audience_prompt,
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_content,
                    },
                ],
                max_completion_tokens=32000,
                model="gpt-4.1",
                temperature=0.9,
            )
            self.logger.info(f"Azure OpenAI response: {response}")
        except APIError as e:
            raise ConnectionError(f"Azure OpenAI API error: {e}") from e

        if not response.choices or response.choices[0].message.content is None:
            self.logger.warning(
                f"Empty response from Azure OpenAI, "
                f"finish_reason={getattr(response.choices[0], 'finish_reason', 'N/A') if response.choices else 'no choices'}"
            )
            raise ValueError("Azure OpenAI returned empty content")

        self.logger.info(
            f"Azure OpenAI response: {response.choices[0].message.content}"
        )
        return response.choices[0].message.content

    def generate(
        self,
        niche: str,
        keyword: str,
        channel: IDistributionChannel,
        persona=None,
        style=None,
        locale: str = "en",
        **kwargs,
    ) -> dict:
        """Generate content using Azure OpenAI.

        Raises:
            ConnectionError: When Azure OpenAI API is unreachable.
            ValueError: When response is empty or invalid JSON.
        """
        raw_result = self._call_llm(
            niche,
            keyword,
            channel,
            persona,
            style,
            locale,
            blog_url=kwargs.get("blog_url", ""),
            copy_style_prompt=kwargs.get("copy_style_prompt"),
            persona_prompt=kwargs.get("persona_prompt"),
            audience_prompt=kwargs.get("audience_prompt"),
            image_base64=kwargs.get("image_base64"),
        )
        try:
            json_equiv = json.loads(raw_result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Azure OpenAI returned invalid JSON: {e}") from e

        return json_equiv
