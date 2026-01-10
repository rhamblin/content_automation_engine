from abc import ABC, abstractmethod

class IBaseProviderWithName(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider"""
        pass