"""Shared image utilities."""

import base64
import random
from pathlib import Path

from common.app_logger import AppLogger

logger = AppLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def pick_random_image(folder_path: str) -> str | None:
    """Pick a random image from *folder_path* and return base64-encoded content.

    Returns None (with a warning) when the folder doesn't exist or is empty.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        logger.warning("reference_images not found: %s", folder_path)
        return None

    images = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    if not images:
        logger.warning("No images found in: %s", folder_path)
        return None

    chosen = random.choice(images)
    logger.info("Picked reference image: %s", chosen.name)
    return base64.b64encode(chosen.read_bytes()).decode()
