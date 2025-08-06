from ..base import IImageProvider
import requests
import os

class UnsplashImageProvider(IImageProvider):
    def generate_image(self, keywords: str) -> str:
        # Placeholder implementation for make a GET call to 
        # https://api.unsplash.com/search/photos
        # with query as the keyword and niche commas separated
        # the access key would be used for authN/authZ
        # take random one
        ACCESS_KEY = self.__get_api_key()
        url = f"https://api.unsplash.com/search/photos"
        payload = {'query': keywords}
        headers = {'Authorization: Client-ID': ACCESS_KEY}

        response = requests.get(url, params=payload, headers=headers)

        # parse output and get an image

        # download image to our blob storage



        return f"https://example.com/image.png"
    
    def __get_api_key(self) -> str:
        secret_path = os.getenv('UNSPLASH_ACCESSKEY')
        unsplash_access_key = ""

        with open(secret_path, 'r') as f:
            unsplash_access_key = f.read().strip()

        return unsplash_access_key