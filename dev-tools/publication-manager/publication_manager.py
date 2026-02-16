"""Publication Manager — orchestrator (all I/O lives here)."""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "get-pin-ids"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "src"))

from auth import PINTEREST_API_URL, get_access_token
from common.app_logger import AppLogger
from common.evaluators.publication_evaluator import PublicationThresholds

from config import load_request
from publication_manager_service import PublicationManagerService

logger = AppLogger(__name__)


# ── Pinterest API helpers (I/O) ──────────────────────────────────────────────


def fetch_all_pins(access_token: str) -> list[dict]:
    """Fetch all pins from the account."""
    pins = []
    headers = {"Authorization": f"Bearer {access_token}"}
    bookmark = None

    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark

        response = requests.get(
            f"{PINTEREST_API_URL}/pins", headers=headers, params=params
        )
        if not response.ok:
            break

        data = response.json()
        pins.extend(data.get("items", []))
        bookmark = data.get("bookmark")
        if not bookmark:
            break

    return pins


def fetch_pin_analytics(access_token: str, pin_id: str, days: int = 7) -> dict:
    """Fetch analytics for a single pin."""
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/pins/{pin_id}/analytics", headers=headers, params=params
    )

    if not response.ok:
        return {}

    data = response.json()
    daily_metrics = data.get("all", {}).get("daily_metrics", [])

    impressions = 0
    clicks = 0
    saves = 0

    for day in daily_metrics:
        m = day.get("metrics", {})
        impressions += m.get("IMPRESSION", 0)
        clicks += m.get("OUTBOUND_CLICK", 0)
        saves += m.get("SAVE", 0)

    return {"impressions": impressions, "clicks": clicks, "saves": saves}


# ── Display helpers ──────────────────────────────────────────────────────────


def print_results_table(results: list) -> None:
    """Print evaluation results in a formatted table."""
    if not results:
        print("No results.")
        return

    print(
        f"\n{'Title':<35} {'Impr':<10} {'Clicks':<8} {'Saves':<8} "
        f"{'CTR':<8} {'Save%':<8} {'Action':<18} {'Reason'}"
    )
    print("-" * 140)

    for r in results:
        m = r.metrics
        print(
            f"{r.title[:34]:<35} "
            f"{m['impressions']:<10,} "
            f"{m['clicks']:<8,} "
            f"{m['saves']:<8,} "
            f"{m['ctr']:<7.2f}% "
            f"{m['save_rate']:<7.2f}% "
            f"{r.action:<18} "
            f"{r.reason}"
        )


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    data_file = Path(__file__).parent / "data" / "example.json"
    request = load_request(data_file)

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        logger.error(f"Auth error: {e}")
        sys.exit(1)

    thresholds = PublicationThresholds(
        min_impressions=request.min_impressions,
        high_ctr=request.high_ctr,
        low_ctr=request.low_ctr,
        high_save_rate=request.high_save_rate,
        low_save_rate=request.low_save_rate,
    )
    service = PublicationManagerService(thresholds)

    logger.info("Fetching pins...")
    pins = fetch_all_pins(access_token)
    if request.limit:
        pins = pins[: request.limit]
    logger.info(f"Found {len(pins)} pins. Fetching analytics ({request.days} days)...")

    results = []
    for i, pin in enumerate(pins):
        pin_id = pin.get("id")
        title = pin.get("title", "Untitled") or "Untitled"
        logger.info(f"  [{i + 1}/{len(pins)}] {pin_id}")

        metrics = fetch_pin_analytics(access_token, pin_id, request.days)
        result = service.evaluate_pin(pin_id, title, pin.get("link", ""), metrics)
        results.append(result)
        time.sleep(0.3)

    if request.actionable:
        results = [r for r in results if r.action != "none"]

    if request.output_json:
        json_results = [
            {
                "pin_id": r.pin_id,
                "title": r.title,
                "action": r.action,
                "reason": r.reason,
                "metrics": r.metrics,
            }
            for r in results
        ]
        print(json.dumps(json_results, indent=2))
    else:
        actions = {}
        for r in results:
            actions[r.action] = actions.get(r.action, 0) + 1

        print(f"\nEvaluated {len(results)} pins:")
        for action, count in sorted(actions.items()):
            print(f"  {action}: {count}")

        print_results_table(results)


if __name__ == "__main__":
    main()
