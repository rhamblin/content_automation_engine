"""Shared image utilities."""

import base64
import random
from pathlib import Path

from common.app_logger import AppLogger

logger = AppLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_images(folder_path: str) -> list[Path]:
    """Return all image files in *folder_path*, sorted by name.

    Returns an empty list when the folder doesn't exist or has no images.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        logger.warning("reference_images not found: %s", folder_path)
        return []

    images = sorted(f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS)
    if not images:
        logger.warning("No images found in: %s", folder_path)
    return images


def pick_random_image(folder_path: str) -> tuple[str, str] | tuple[None, None]:
    """Pick a random image from *folder_path*.

    Returns:
        (base64_str, absolute_file_path) on success, or (None, None) when
        the folder doesn't exist or is empty.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        logger.warning("reference_images not found: %s", folder_path)
        return None, None

    images = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    if not images:
        logger.warning("No images found in: %s", folder_path)
        return None, None

    chosen = random.choice(images)
    logger.info("Picked reference image: %s", chosen.name)
    return base64.b64encode(chosen.read_bytes()).decode(), str(chosen)
