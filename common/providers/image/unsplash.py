from ..base import IImageProvider, ImageResult
import requests
import os
import http

#TODO: Add logging 
class UnsplashImageProvider(IImageProvider):
    def generate_image(self, keywords: str) -> ImageResult:
        ACCESS_KEY = self.__get_api_key()
        url = f"https://api.unsplash.com/search/photos"
        payload = {'query': keywords}
        headers = {
            'Authorization': 'Client-ID ' + ACCESS_KEY,
            'Accept-Version': 'v1'
            }

        response = requests.get(url, params=payload, headers=headers)

        if response.status_code == http.HTTPStatus.OK:

            #TODO: Handle case where no photos are returned i.e. response.json().results is empty
            first_photo = response.json().results[0]

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
            print(error_msg)
        else:
            error_msg = "There was an error in UnsplashImageProvider"
            print(error_msg)
            raise requests.HTTPError(error_msg, response=response)

    def __get_api_key(self) -> str:
        secret_path = os.getenv('UNSPLASH_ACCESSKEY')
        unsplash_access_key = ""

        with open(secret_path, 'r') as f:
            unsplash_access_key = f.read().strip()

        return unsplash_access_key