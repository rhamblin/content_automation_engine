from ..base import ITextProvider
from openai import OpenAI
import os

client = OpenAI()
client.api_key = None  # will be set by get_api_key()

def __get_api_key() -> str:
    secret_path = os.getenv('OPENAI_API_KEY')
    openai_api_key = ""

    with open(secret_path, 'r') as f:
        openai_api_key = f.read().strip()

    return openai_api_key

class OpenAITextProvider(ITextProvider):

    def __get_system_message(self) -> str:
        return (
            "You are a Pinterest marketing expert specializing in creating high-engagement Pins. "
            "Understand the interests and behaviors of Pinterest users in each niche, and tailor language to resonate with their aspirations and aesthetics. "
            "Use Pinterest SEO best practices—incorporate power words, relevant trending hashtags, and a clear call-to-action. "
            "Craft titles that maximize click-through rates and descriptions that highlight benefits, evoke emotion, and encourage saves and shares."
        )

    def generate_text(self, niche: str, keyword: str) -> dict:
        """
        Generates a high-engagement, keyword-rich Post title for the given niche and keywords on the given channel.
        """
        # add in formatting instruction for title and description output
        messages = [
            {"role": "system", "content": self.get_system_message()},
            {"role": "user", "content": (
                f"Niche: {niche}\n"
                f"Primary keywords: {keyword}\n"
                "Audience: Pinterest users interested in this niche\n"
                "Task: Generate a clickable, under 50-character Pin title optimized for engagement and discovery."
            )}
        ]
        client.api_key = __get_api_key()

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.6,
            max_tokens=60
        )
        return response.choices[0].message.content.strip()

    def generate_pin_description(
        self,
        niche: str,
        keywords: str,
        tone: str = "warm and friendly",
        cta: str = "") -> str:
        """
        Generates a concise, benefit-focused Pinterest Pin description for the given niche,
        keywords, tone, and optional call-to-action.
        """
        messages = [
            {"role": "system", "content": self.__get_system_message()},
            {"role": "user", "content": (
                f"Niche: {niche}\n"
                f"Primary keywords: {keywords}\n"
                f"Tone: {tone}\n"
                "Audience: Pinterest users seeking inspiration in this niche\n"
                "Task: Craft a description (≤200 chars) that weaves in keywords, highlights benefits, "
                "uses power words, evokes emotion, and ends with the CTA or a trending hashtag. "
                f"CTA: {cta}"
            )}
        ]

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.6,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()