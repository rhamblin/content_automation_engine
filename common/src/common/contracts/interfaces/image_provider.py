from abc import abstractmethod
from .base_provider_with_name import IBaseProviderWithName


class IBlobStorage(IBaseProviderWithName):
    @abstractmethod
    def fetch_image(self, keyword: str) -> str:
        pass
