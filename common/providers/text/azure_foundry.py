from . import ITextProvider
from openai import AzureOpenAI
import os
import json

class AzureFoundryTextProvider(ITextProvider):

    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        model_name = "gpt-5-nano"

        client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint=self.__get_endpoint(),
            api_key=self.__get_subscription_key(),
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": self.__get_system_message(),
                },
                {
                    "role": "user",
                    "content": (
                        f"Niche: {niche}\n"
                        f"Primary keyword: {keyword}\n"
                    ),
                }
            ],
            max_completion_tokens=16000,
            model=model_name
        )

        raw_result = response.choices[0].message.content
        json_equiv = json.loads(raw_result)

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
    
    def __get_endpoint(self):
        return os.getenv("AZURE_FOUNDRY_ENDPOINT")

    def __get_subscription_key(self):
        secret_path = os.getenv('AZURE_FOUNDRY_PROJ_DEFAULT_API_KEY')
        azure_foundry_api_key = ""

        with open(secret_path, 'r') as f:
            azure_foundry_api_key = f.read().strip()

        return azure_foundry_api_key