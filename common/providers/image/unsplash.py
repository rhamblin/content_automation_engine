from . import IImageProvider, ImageResult
import requests
import os
import http
import logging

class UnsplashImageProvider(IImageProvider):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False

    def generate_image(self, niche: str, keyword: str) -> ImageResult:
        self.logger.info(f"Generating image for keyword: {keyword}")

        ACCESS_KEY = self.__get_api_key()
        url = f"https://api.unsplash.com/search/photos"
        payload = {'query': keyword}
        headers = {
            'Authorization': 'Client-ID ' + ACCESS_KEY,
            'Accept-Version': 'v1'
            }

        response = requests.get(url, params=payload, headers=headers)

        if response.status_code == http.HTTPStatus.OK:
            self.logger.info("Image fetched successfully from Unsplash")
            json_data = response.json()

            if not json_data:
                error_msg = "No photos found for the given keywords."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            first_photo = json_data.results[0]
            self.logger.info(f"Selected photo by {first_photo.user.name}: {first_photo.urls.regular}")

            return ImageResult(
                regular_url=first_photo.urls.regular,
                download_link=first_photo.links.download,
                author_name=first_photo.user.name,
                author_username=first_photo.user.username,
                utm_parameters='utm_source=content-engine&utm_medium=referral'
            )
        elif response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
            # TODO: Handle rate limiting
            error_msg = "Rate limit exceeded. Please try again later."
            self.logger.error(error_msg)
        else:
            error_msg = "There was an error in UnsplashImageProvider"
            self.logger.error(error_msg)
            raise requests.HTTPError(error_msg, response=response)

    def __get_api_key(self) -> str:
        self.logger.info("Retrieving Unsplash API key")
        secret_path = os.getenv('UNSPLASH_ACCESS_KEY')
        unsplash_access_key = ""

        with open(secret_path, 'r') as f:
            unsplash_access_key = f.read().strip()
            self.logger.info("Unsplash API key retrieved successfully")

        return unsplash_access_key