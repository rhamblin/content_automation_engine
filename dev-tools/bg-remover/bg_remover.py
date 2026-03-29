"""Background Remover — orchestrator (all I/O lives here)."""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from common.app_logger import AppLogger
from common.utils.images import collect_images
from common.workflows.bg_remover import BgRemoverService

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config

logger = AppLogger(__name__)


def main():
    print("Background Remover\n")

    data_file = Path(__file__).parent / "data" / "input.json"
    if len(sys.argv) > 1:
        data_file = Path(sys.argv[1])

    if not data_file.exists():
        logger.error("Data file not found: %s", data_file)
        sys.exit(1)

    config = load_config(data_file)

    # Collect source images
    images = collect_images(config.reference_images)
    if not images:
        logger.error("No images found in: %s", config.reference_images)
        sys.exit(1)

    logger.info(
        "Processing %d image(s) for '%s' with background %s",
        len(images), config.keyword, config.background_color,
    )

    # Create timestamped output folder
    slug = config.keyword.lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(config.output_folder) / f"{slug}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    service = BgRemoverService()
    manifest = []
    saved, errors = 0, 0

    for img_path in images:
        try:
            source = Image.open(img_path).convert("RGB")
            result = service.process(
                source=source,
                background_color=config.background_color,
                source_name=img_path.name,
            )
            if result is None:
                errors += 1
                continue

            short_hash = hashlib.md5(img_path.name.encode()).hexdigest()[:4]
            out_name = f"{slug}_{short_hash}.jpg"
            out_path = output_dir / out_name
            result.save(out_path, "JPEG", quality=95)
            logger.info("Saved: %s", out_path)
            saved += 1

            manifest.append({
                "keyword": config.keyword,
                "source_image": str(img_path),
                "output_file": out_name,
                "background_color": config.background_color,
            })

        except Exception as e:
            logger.error("Error processing %s: %s", img_path.name, e)
            errors += 1

    # Write manifest
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info("Manifest written: %s", manifest_path)

    logger.info(
        "Done — %d saved, %d errors. Output: %s",
        saved, errors, output_dir,
    )


if __name__ == "__main__":
    main()
