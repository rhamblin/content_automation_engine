from ..base import IModelProvider

class OpenAIModelProvider(IModelProvider):
    def generate_text(self, prompt: str) -> str:
        return f"Generated text for {prompt}"
