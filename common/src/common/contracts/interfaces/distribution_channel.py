from abc import abstractmethod

from .base_provider_with_name import IBaseProviderWithName


class IDistributionChannel(IBaseProviderWithName):
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def publish(self, title: str, content: str, image_url: str, **kwargs) -> dict:
        """Publish content to the distribution channel.

        Returns:
            dict with keys: post_id, url, status
        """
        pass
