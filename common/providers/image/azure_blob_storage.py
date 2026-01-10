from common.contracts import IImageProvider
from common.contracts.database_models import Keyword
from azure.storage.blob import BlobServiceClient, ContainerClient
import random

class AzureBlobStorageImageProvider(IImageProvider):

    def __init__(self, blob_client: BlobServiceClient, logger):
        self.blob_client = blob_client
        self.logger = logger

    def provider_name(self) -> str:
        return "azure_blob_storage"
    
    def fetch_image(self, keyword: Keyword) -> str:
        container_name = "images"
        prefix = f"keywords/{keyword.keyword_id}/"

        try:
            container_client: ContainerClient = self.blob_client.get_container_client(container_name)

            # List all blobs in the keyword folder
            blob_list = container_client.list_blobs(name_starts_with=prefix)

            # Filter to get only image files (exclude .txt files)
            image_blobs = [
                blob for blob in blob_list
                if not blob.name.endswith('.txt')
            ]

            if not image_blobs:
                self.logger.error(f"No images found for keyword {keyword.name} at path {prefix}")
                raise ValueError(f"No images found for keyword {keyword.name}")

            # Randomly select an image
            selected_blob = random.choice(image_blobs)

            # Construct the blob URL
            blob_url = f"{container_client.url}/{selected_blob.name}"

            self.logger.info(f"Selected image {selected_blob.name} for keyword {keyword}")

            return blob_url

        except Exception as e:
            self.logger.error(f"Error fetching image for keyword {keyword.name}: {str(e)}")
            raise
    
    