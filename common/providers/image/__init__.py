from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ImageResult:
    regular_url: str
    download_link: str
    author_name: str
    author_username: str
    utm_parameters: str

class IImageProvider(ABC):
    @abstractmethod
    def generate_image(self, niche: str, keyword: str) -> ImageResult:
        pass
