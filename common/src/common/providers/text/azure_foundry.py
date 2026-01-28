import json

from openai import APIError, AzureOpenAI

from common.contracts.interfaces import ITextProvider


class AzureFoundryTextProvider(ITextProvider):
    """Azure OpenAI text provider.

    Raises:
        ConnectionError: When Azure OpenAI API is unreachable.
        ValueError: When response is empty or invalid JSON.
    """

    PROVIDER_NAME = "azure_foundry"

    def __init__(self, azure_open_ai_client: AzureOpenAI):
        self.client = azure_open_ai_client

    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        """Generate text content using Azure OpenAI.

        Raises:
            ConnectionError: When Azure OpenAI API is unreachable.
            ValueError: When response is empty or invalid JSON.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.__get_system_message(),
                    },
                    {
                        "role": "user",
                        "content": (f"Niche: {niche}\n" f"Primary keyword: {keyword}\n"),
                    },
                ],
                max_completion_tokens=16000,
                model="gpt-5-nano",
            )
        except APIError as e:
            raise ConnectionError(f"Azure OpenAI API error: {e}") from e

        if not response.choices:
            raise ValueError("Azure OpenAI returned no choices")

        raw_result = response.choices[0].message.content
        try:
            json_equiv = json.loads(raw_result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Azure OpenAI returned invalid JSON: {e}") from e

        return json_equiv

    def __get_system_message(self) -> str:
        return (
            """
            You are a Pinterest marketing expert specializing in creating high-engagement Pins that drive clicks, saves, and shares."
            You understand Pinterest user behavior by niche, including aesthetics, aspirations, seasonal intent, and discovery mindset.

            You apply Pinterest SEO best practices, naturally incorporating high-intent keywords, power words, relevant or trending hashtags, and emotionally resonant language.

            GOALS:
            1. Craft scroll-stopping titles that maximize click-through rate (CTR).
            2. Write benefit-driven descriptions that evoke emotion and encourage saves and shares.
            3. Create a clear, action-oriented CTA aligned with Pinterest behaviors.

            TASK:
            Given a Pin topic and target niche, generate:
            - title: concise, click-optimized
            - description: ≤200 characters, keyword-rich, benefit-focused, emotionally engaging, ending with a CTA or trending hashtag
            - cta: short, explicit, action-oriented

            STRICT OUTPUT RULES:
            - Output ONLY valid JSON
            - No markdown, no explanations
            - JSON keys must be exactly: title, description, cta
            - Description must be 200 characters or fewer
            """
        )