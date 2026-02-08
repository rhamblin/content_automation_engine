import json

from openai import APIError, AzureOpenAI

from common.contracts.interfaces import IDistributionChannel, ITextProvider


class AzureFoundryTextProvider(ITextProvider):
    """Azure OpenAI text provider.

    Raises:
        ConnectionError: When Azure OpenAI API is unreachable.
        ValueError: When response is empty or invalid JSON.
    """

    PROVIDER_NAME = "azure_foundry"

    def __init__(self, azure_open_ai_client: AzureOpenAI):
        self.client = azure_open_ai_client

    def generate_text(
        self, niche: str, keyword: str, channel: IDistributionChannel
    ) -> dict:
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
                        "content": channel.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Niche: {niche}\n" f"Primary keyword: {keyword}\n"
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
