import random

from azure.storage.blob import BlobServiceClient, ContainerClient

from common.app_logger import AppLogger
from common.contracts.database_models import Keyword
from common.contracts.interfaces import IBlobStorage


class AzureBlobStorageProvider(IBlobStorage):
    PROVIDER_NAME = "azure_blob_storage"
    IMAGE_PREFIX = "keywords/{keyword_external_id}/"

    def __init__(self, blob_client: BlobServiceClient):
        self.logger = AppLogger(__name__)
        self.blob_client = blob_client
        self.__container_name = "images"

    def fetch_image_uri(self, keyword: Keyword) -> str:
        image_path_prefix = self.IMAGE_PREFIX.format(
            keyword_external_id=keyword.external_id
        )

        container_client: ContainerClient = self.blob_client.get_container_client(
            self.__container_name
        )

        if not container_client.exists():
            raise FileNotFoundError(
                f"Blob container '{self.__container_name}' not found"
            )

        blob_list = container_client.list_blobs(name_starts_with=image_path_prefix)

        identifier_text_blob_client = container_client.get_blob_client(
            "".join([image_path_prefix, keyword.term, ".txt"])
        )

        if not identifier_text_blob_client:
            identifier_text_blob_client.upload_blob("", overwrite=True)

        # Filter to get only image files (exclude .txt files)
        image_blobs = [blob for blob in blob_list if not blob.name.endswith(".txt")]

        if not image_blobs:
            raise FileNotFoundError(
                f"No images found for keyword {keyword.term} with path {image_path_prefix}"
            )

        # Randomly select an image
        selected_blob = random.choice(image_blobs)

        # Construct the blob URL

        selected_blob_client = container_client.get_blob_client(selected_blob.name)
        selected_url = selected_blob_client.url  # full URL

        self.logger.info(f"Selected image {selected_url} for keyword {keyword.term}")

        return selected_url
