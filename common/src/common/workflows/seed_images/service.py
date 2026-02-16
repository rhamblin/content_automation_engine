"""Business logic for uploading seed images from tenant config into blob storage."""

import mimetypes
from pathlib import Path
from uuid import UUID

from azure.storage.blob import BlobServiceClient, ContainerClient
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from common.app_logger import AppLogger
from common.contracts.database_models import Keyword
from common.repositories.tenant_scoped import NicheRepository

logger = AppLogger("seed-images")

CONTAINER_NAME = "images"
BLOB_PREFIX = "keywords/{keyword_external_id}/"


class SeedImageService:
    """Resolves slug-based seed-image folders to keyword UUIDs and uploads to blob storage."""

    def __init__(self, blob_client: BlobServiceClient, session: AsyncSession):
        self._container_client: ContainerClient = blob_client.get_container_client(
            CONTAINER_NAME
        )
        self._session = session

    async def upload_niche_seed_images(
        self, tenant_id: UUID, niche_id: UUID, niche_dir: Path
    ) -> int:
        """Upload seed images for a single niche. Returns count of uploaded files."""
        seed_dir = niche_dir / "seed-images"
        if not seed_dir.exists():
            return 0

        # Ensure container exists
        if not self._container_client.exists():
            self._container_client.create_container()
            logger.info(f"Created blob container '{CONTAINER_NAME}'")

        # Build slug → keyword map from DB
        niche_repo = NicheRepository(self._session, tenant_id)
        keywords = await niche_repo.get_keywords(niche_id)
        slug_map: dict[str, Keyword] = {
            _to_slug(kw.term): kw for kw in keywords
        }

        uploaded = 0
        for slug_folder in sorted(seed_dir.iterdir()):
            if not slug_folder.is_dir():
                continue

            slug = slug_folder.name.lower()
            keyword = slug_map.get(slug)
            if not keyword:
                logger.warning(
                    f"No keyword matches slug '{slug_folder.name}', skipping"
                )
                continue

            prefix = BLOB_PREFIX.format(keyword_external_id=keyword.external_id)

            # Upload each image file
            for img_file in sorted(slug_folder.iterdir()):
                if not img_file.is_file():
                    continue
                blob_name = f"{prefix}{img_file.name}"
                content_type = (
                    mimetypes.guess_type(img_file.name)[0] or "application/octet-stream"
                )
                self._upload_blob(blob_name, img_file.read_bytes(), content_type)
                uploaded += 1
                logger.info(f"Uploaded {blob_name}")

            # Create identifier .txt file (matches runtime convention)
            txt_name = f"{prefix}{keyword.term.replace(' ', '_')}.txt"
            self._upload_blob(txt_name, b"", "text/plain")
            logger.info(f"Created identifier {txt_name}")

        return uploaded

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=5),
        reraise=True,
    )
    def _upload_blob(self, blob_name: str, data: bytes, content_type: str) -> None:
        from azure.storage.blob import ContentSettings

        blob_client = self._container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )


def _to_slug(term: str) -> str:
    """Convert keyword term to slug: lowercase, spaces → hyphens."""
    return term.lower().replace(" ", "-")
