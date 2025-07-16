from ..base import IImageProvider

class OpenAIImageProvider(IImageProvider):
    def generate_image(self, prompt: str) -> str:
        # Placeholder for OpenAI image generation
        return f"https://example.com/image/{hash(prompt)}.png"
