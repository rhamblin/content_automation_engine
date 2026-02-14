from abc import ABC, abstractmethod


class IBaseProviderWithName(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...
