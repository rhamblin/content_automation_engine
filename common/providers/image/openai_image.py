from ..base import IImageProvider


class OpenAIImageProvider(IImageProvider):
    def generate_image(self, prompt: str) -> str:
        # Placeholder implementation
        return f"https://example.com/image/{hash(prompt) % 10000}.png"
