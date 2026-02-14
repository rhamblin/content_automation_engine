import random

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, ContainerClient

from common.app_logger import AppLogger
from common.contracts.database_models import Keyword
from common.contracts.interfaces import IBlobStorage


class AzureBlobStorageProvider(IBlobStorage):
    """Azure Blob Storage provider.

    Raises:
        ConnectionError: When Azure Blob Storage is unreachable.
        FileNotFoundError: When container or blobs are not found.
    """

    @property
    def provider_name(self) -> str:
        return "azure_blob_storage"
    IMAGE_PREFIX = "keywords/{keyword_external_id}/"

    def __init__(self, blob_client: BlobServiceClient):
        self.logger = AppLogger(__name__)
        self.container_name = "images"
        self.container_client: ContainerClient = blob_client.get_container_client(
            self.container_name
        )

    def fetch_image_uri(self, keyword: Keyword) -> str:
        """Fetch a random image URI for the given keyword.

        Raises:
            ConnectionError: When Azure Blob Storage is unreachable.
            FileNotFoundError: When container or images are not found.
        """
        image_path_prefix = self.IMAGE_PREFIX.format(
            keyword_external_id=keyword.external_id
        )

        try:
            if not self.container_client.exists():
                raise FileNotFoundError(
                    f"Blob container '{self.container_name}' not found"
                )

            blob_list = self.container_client.list_blobs(
                name_starts_with=image_path_prefix
            )

            identifier_text_blob_client = self.container_client.get_blob_client(
                "".join([image_path_prefix, keyword.term.replace(" ", "_"), ".txt"])
            )

            if not identifier_text_blob_client:
                identifier_text_blob_client.upload_blob("", overwrite=True)

            image_blobs = [blob for blob in blob_list if not blob.name.endswith(".txt")]

            if not image_blobs:
                raise FileNotFoundError(
                    f"No images found for keyword {keyword.term} at {image_path_prefix}"
                )

            selected_blob = self._select_blob(image_blobs)
            selected_url = self.container_client.get_blob_client(selected_blob.name).url

        except AzureError as e:
            raise ConnectionError(f"Azure Blob Storage error: {e}") from e

        self.logger.info(f"Selected image {selected_url} for keyword {keyword.term}")
        return selected_url

    def _select_blob(self, blobs):
        return random.choice(blobs)
