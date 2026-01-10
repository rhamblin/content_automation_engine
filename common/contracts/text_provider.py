from abc import ABC, abstractmethod

class ITextProvider(ABC):
    @abstractmethod
    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        pass
