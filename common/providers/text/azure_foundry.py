from common.contracts import ITextProvider
from openai import AzureOpenAI
import json

class AzureFoundryTextProvider(ITextProvider):
    def __init__(self, azure_open_ai_client: AzureOpenAI, logger):
        self.client = azure_open_ai_client
        self.logger = logger

    def provider_name(self) -> str:
        return "azure_foundry"
    
    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        self.logger.info(f"Generating text for niche='{niche}', keyword='{keyword}', channel='{channel}'")
        model_name = "gpt-5-nano"

        self.logger.info(f"Calling Azure OpenAI with model '{model_name}'")
        response = self.client.chat.completions.create(
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

        self.logger.info(f"Successfully generated text for niche='{niche}', keyword='{keyword}', channel='{channel}'")
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