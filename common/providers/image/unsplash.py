from ..base import IImageProvider


class UnsplashImageProvider(IImageProvider):
    def generate_image(self) -> str:
        # Placeholder implementation
        return f"https://example.com/image.png"
