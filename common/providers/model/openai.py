from ..base import ITextProvider


class OpenAITextProvider(ITextProvider):
    def generate_text(self, prompt: str) -> str:
        # Placeholder text generation
        return f"Generated text for: {prompt}"
