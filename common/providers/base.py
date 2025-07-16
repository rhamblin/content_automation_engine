from abc import ABC, abstractmethod

class IImageProvider(ABC):
    @abstractmethod
    def generate_image(self, prompt: str) -> str:
        """Generate an image and return a URL"""
        raise NotImplementedError

class IModelProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Generate text"""
        raise NotImplementedError

class IChannel(ABC):
    @abstractmethod
    def post(self, title: str, description: str, asset_url: str, hashtags: list[str]):
        """Post content to a channel"""
        raise NotImplementedError
