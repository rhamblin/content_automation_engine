from abc import abstractmethod

from ..database_models import Keyword
from .base_provider_with_name import IBaseProviderWithName


class IBlobStorage(IBaseProviderWithName):
    @abstractmethod
    def fetch_image_uri(self, keyword: Keyword) -> str:
        pass
