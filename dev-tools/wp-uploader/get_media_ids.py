"""Look up WordPress media IDs for .jpg files in a directory."""

import csv
import re
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings

OUTPUT_FILE = Path(__file__).parent / "input/content_topics.csv"

NICHE = "food"  # ← hardcoded niche


def filename_to_keyword(filename: str) -> str:
    """
    lava_cakes1.jpg -> lava cakes
    coconut_pancakes1.jpg -> coconut pancakes
    """
    stem = Path(filename).stem
    stem = re.sub(r"\d+$", "", stem)  # remove trailing numbers
    return stem.replace("_", " ").strip()


def get_media_id(
    session: requests.Session, api_url: str, filename: str
) -> tuple[int | None, str]:
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
    session = requests.Session()
    session.auth = HTTPBasicAuth(settings.wp_username, settings.wp_app_password)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["niche", "keyword", "image_url", "media_id"])

        for jpg in image_dir.glob("*.jpg"):
            media_id, wp_url = get_media_id(session, settings.wp_site_url, jpg.stem)
            keyword = filename_to_keyword(jpg.name)

            writer.writerow([NICHE, keyword, wp_url, media_id or ""])
            print(f"{keyword} -> {media_id or 'not found'}")

    print(f"\nResults written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
