from abc import abstractmethod

from .base_provider_with_name import IBaseProviderWithName
from .distribution_channel import IDistributionChannel


class ITextProvider(IBaseProviderWithName):
    @abstractmethod
    def generate_text(self, niche: str, keyword: str, channel: IDistributionChannel) -> dict:
        pass
