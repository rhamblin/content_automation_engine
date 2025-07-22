from abc import ABC, abstractmethod


class IImageProvider(ABC):
    @abstractmethod
    def generate_image(self, keyword: str) -> str:
        pass


class ITextProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass


class IChannel(ABC):
    @abstractmethod
    def post(self, title: str, description: str, image_url: str, **kwargs) -> bool:
        pass
