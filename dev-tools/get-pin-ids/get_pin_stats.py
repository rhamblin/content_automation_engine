"""Fetch campaign stats for a Pinterest pin for yesterday."""

import argparse
import json
import sys
from datetime import datetime, timedelta

import requests

from auth import PINTEREST_API_URL, get_access_token


def get_pin_analytics(access_token: str, pin_id: str) -> dict | None:
    """Fetch analytics for a pin for yesterday."""
    yesterday = datetime.now() - timedelta(days=1)
    start_date = yesterday.strftime("%Y-%m-%d")
    end_date = start_date

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK,VIDEO_START,VIDEO_MRC_VIEW",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/pins/{pin_id}/analytics",
        headers=headers,
        params=params,
    )

    if not response.ok:
        print(f"Failed to fetch analytics: {response.status_code} - {response.text}")
        return None

    return response.json()


def get_pin_details(access_token: str, pin_id: str) -> dict | None:
    """Fetch pin details."""
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(
        f"{PINTEREST_API_URL}/pins/{pin_id}",
        headers=headers,
    )

    if not response.ok:
        print(f"Failed to fetch pin: {response.status_code} - {response.text}")
        return None

    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Get Pinterest pin stats for yesterday")
    parser.add_argument("pin_id", help="Pinterest pin ID")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    pin_details = get_pin_details(access_token, args.pin_id)
    analytics = get_pin_analytics(access_token, args.pin_id)

    if args.json:
        print(json.dumps({"pin": pin_details, "analytics": analytics}, indent=2))
        return

    if pin_details:
        print(f"\nPin: {pin_details.get('title', 'Untitled')}")
        print(f"ID: {args.pin_id}")
        print(f"Created: {pin_details.get('created_at', 'N/A')}")

    if analytics:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\nStats for {yesterday}:")
        print("-" * 30)

        daily = analytics.get("all", {}).get("daily_metrics", [])
        if daily:
            metrics = daily[0] if daily[0].get("data_status") == "READY" else {}
            for key, value in metrics.items():
                if key not in ("date", "data_status"):
                    print(f"  {key}: {value}")
        else:
            summary = analytics.get("all", {}).get("summary_metrics", {})
            for key, value in summary.items():
                print(f"  {key}: {value}")

        if not daily and not analytics.get("all", {}).get("summary_metrics"):
            print("  No data available for yesterday")
    else:
        print("\nNo analytics data available")


if __name__ == "__main__":
    main()
