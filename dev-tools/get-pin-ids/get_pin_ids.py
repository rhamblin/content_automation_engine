"""Fetch all pins and their IDs from a Pinterest account using OAuth."""

import csv
import sys
from datetime import datetime
from pathlib import Path

import requests

from pinterest_auth.auth import PINTEREST_API_URL, get_access_token

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_all_pins(access_token: str) -> list[dict]:
    """Fetch all pins from the authenticated Pinterest account."""
    pins = []
    headers = {"Authorization": f"Bearer {access_token}"}
    bookmark = None

    print("Fetching pins...")

    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark

        response = requests.get(
            f"{PINTEREST_API_URL}/pins", headers=headers, params=params
        )

        if not response.ok:
            print(f"Failed to fetch pins: {response.status_code} - {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        pins.extend(items)

        print(f"  Fetched {len(items)} pins (total: {len(pins)})")

        bookmark = data.get("bookmark")
        if not bookmark:
            break

    return pins


def save_pins_to_csv(pins: list[dict]) -> Path:
    """Save pins to a timestamped CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = OUTPUT_DIR / f"{timestamp}.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pin_id", "title", "description", "link", "created_at"])

        for pin in pins:
            writer.writerow(
                [
                    pin.get("id", ""),
                    pin.get("title", ""),
                    pin.get("description", "")[:100] if pin.get("description") else "",
                    pin.get("link", ""),
                    pin.get("created_at", ""),
                ]
            )

    return output_file


def main():
    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    pins = get_all_pins(access_token)

    if not pins:
        print("No pins found")
        return

    output_file = save_pins_to_csv(pins)
    print(f"\nSaved {len(pins)} pins to {output_file}")


if __name__ == "__main__":
    main()
