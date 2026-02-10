from abc import abstractmethod
from typing import Any

from .base_provider_with_name import IBaseProviderWithName


class IDistributionChannel(IBaseProviderWithName):
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def render_content(self, source: Any, text_data: dict) -> Any:
        """Render core content for this channel.

        Args:
            source: Source content (Image.Image for visual channels, None for text channels)
            text_data: Text data from text provider (title, content, style, etc.)

        Returns:
            Image.Image: For visual channels (Pinterest, Instagram)
            str: For text channels (WordPress, Medium)
        """
        pass

    @abstractmethod
    def publish(self, title: str, description: str, content: Any, **kwargs) -> dict:
        """Publish content to the distribution channel.

        Args:
            title: Content title
            description: Content description
            content: Rendered content from render_content()

        Returns:
            dict with keys: post_id, url, status
        """
        pass
