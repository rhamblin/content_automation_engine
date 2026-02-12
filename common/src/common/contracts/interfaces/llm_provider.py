from abc import abstractmethod

from .base_provider_with_name import IBaseProviderWithName
from .distribution_channel import IDistributionChannel


class ILLMProvider(IBaseProviderWithName):
    @abstractmethod
    def generate(
        self,
        niche: str,
        keyword: str,
        channel: IDistributionChannel,
        persona=None,
        style=None,
        locale: str = "en",
        **kwargs,
    ) -> dict:
        pass
