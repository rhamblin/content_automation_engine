from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from .base_provider_with_name import IBaseProviderWithName

# Deferred import: database_models → enums → messages → interfaces → here → database_models
if TYPE_CHECKING:
    from ..database_models import Keyword


class IBlobStorage(IBaseProviderWithName):
    @abstractmethod
    def fetch_image_uri(self, keyword: Keyword) -> str:
        pass
