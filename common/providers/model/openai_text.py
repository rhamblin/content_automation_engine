from ..base import IModelProvider


class OpenAIModelProvider(IModelProvider):
    def generate_text(self, prompt: str) -> str:
        # Placeholder text generation
        return f"Generated text for: {prompt}"
