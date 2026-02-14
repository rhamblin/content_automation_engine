"""Look up WordPress media IDs for image files in a directory.

Renames local files with a short UUID prefix to prevent collisions
when matching filenames to WordPress URLs (e.g. "baked_chicken" vs
"lemon_baked_chicken" would both match without unique identifiers).
"""

import csv
import re
import sys
import uuid
from pathlib import Path
from shutil import get_terminal_size

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

OUTPUT_FILE = Path(__file__).parent / "input/content_topics.csv"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".avif", ".webp"}


def _progress_bar(current: int, total: int, width: int = 30) -> str:
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total} ({pct:.0%})"


def filename_to_keyword(filename: str) -> str:
    """
    a1b2c3_lava_cakes1.jpg -> lava cakes
    lava_cakes1.jpg -> lava cakes

    Strips UUID prefix (6-char hex + underscore) and trailing digits.
    """
    stem = Path(filename).stem
    # Strip UUID prefix if present (6 hex chars followed by underscore)
    stem = re.sub(r"^[0-9a-f]{6}_", "", stem)
    # Remove trailing numbers (e.g. "1" in "lava_cakes1")
    stem = re.sub(r"\d+$", "", stem)
    return stem.replace("_", " ").strip()


def ensure_uuid_prefix(filepath: Path) -> Path:
    """Add a 6-char UUID prefix to filename if not already present.

    Returns the (possibly renamed) Path. Skips if prefix already exists.
    """
    stem = filepath.stem
    # Check if already has a 6-char hex prefix
    if re.match(r"^[0-9a-f]{6}_", stem):
        return filepath

    short_id = uuid.uuid4().hex[:6]
    new_name = f"{short_id}_{filepath.name}"
    new_path = filepath.parent / new_name
    filepath.rename(new_path)
    return new_path


def get_media_id(
    session: requests.Session, api_url: str, filename: str
) -> tuple[int | None, str]:
    """Search WordPress media library for a file matching filename."""
    response = session.get(
        f"{api_url}/wp-json/wp/v2/media",
        params={"search": filename, "per_page": 10},
    )

    if not response.ok or not response.json():
        return None, ""

    # Find best match - check if filename appears in source_url or slug
    for media in response.json():
        source_url = media.get("source_url", "")
        slug = media.get("slug", "")
        if filename.lower() in source_url.lower() or filename.lower() in slug.lower():
            return media["id"], source_url

    first = response.json()[0]
    return first["id"], first.get("source_url", "")


def main():
    if len(sys.argv) < 2 or not sys.argv[1]:
        print("Error: MEDIA_FOLDER not provided")
        print("Usage: make wp-media-ids MEDIA_FOLDER=/path/to/images")
        sys.exit(1)

    image_dir = Path(sys.argv[1])
    if not image_dir.exists():
        print(f"Error: Folder not found: {image_dir}")
        sys.exit(1)

    settings = load_dev_settings()
    niche = settings.wp_niche
    session = requests.Session()
    session.auth = HTTPBasicAuth(settings.wp_username, settings.wp_app_password)

    images = [f for f in image_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    total = len(images)

    if total == 0:
        print(f"No image files found in {image_dir}")
        sys.exit(1)

    cols = get_terminal_size().columns
    print("─" * min(cols, 60))
    print(f"WP Media ID Lookup")
    print(f"Folder: {image_dir}  |  Images: {total}")
    print("─" * min(cols, 60))

    found = 0
    not_found = 0

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["niche", "keyword", "image_url", "media_id"])

        for i, img_path in enumerate(sorted(images)):
            # Ensure UUID prefix for collision prevention
            img_path = ensure_uuid_prefix(img_path)

            keyword = filename_to_keyword(img_path.name)
            media_id, wp_url = get_media_id(session, settings.wp_site_url, img_path.stem)

            writer.writerow([niche, keyword, wp_url, media_id or ""])

            status = "✓" if media_id else "✗"
            if media_id:
                found += 1
            else:
                not_found += 1

            print(f"  {status} ({i+1}/{total}) {keyword:<30} -> {media_id or 'not found'}")
            print(f"    {_progress_bar(i + 1, total)}")

    print("")
    print("─" * min(cols, 60))
    print(f"  Found: {found}  |  Not found: {not_found}  |  Total: {total}")
    print(f"  Output: {OUTPUT_FILE}")
    print("─" * min(cols, 60))


if __name__ == "__main__":
    main()
