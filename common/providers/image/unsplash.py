from ..base import IImageProvider


class UnsplashImageProvider(IImageProvider):
    def generate_image(self) -> str:
        # Placeholder implementation for make a GET call to 
        # https://api.unsplash.com/search/photos
        # with query as the keyword and niche commas separated
        # the access key would be used for authN/authZ
        # take random one
        return f"https://example.com/image.png"
        