from ..base import IChannel

class PinterestChannel(IChannel):
    def post(self, title: str, description: str, asset_url: str, hashtags: list[str]):
        print(f"Posting to Pinterest: {title}")
        return True
