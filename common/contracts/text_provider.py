from abc import ABC, abstractmethod
from .base_provider_with_name import IBaseProviderWithName

class ITextProvider(ABC, IBaseProviderWithName):
    @abstractmethod
    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        pass