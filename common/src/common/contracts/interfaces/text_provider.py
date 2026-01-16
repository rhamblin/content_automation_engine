from abc import abstractmethod

from .base_provider_with_name import IBaseProviderWithName


class ITextProvider(IBaseProviderWithName):
    @abstractmethod
    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        pass
