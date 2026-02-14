"""Publication Manager - evaluate organic pin performance and recommend actions."""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "get-pin-ids"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "src"))

from auth import PINTEREST_API_URL, get_access_token
from common.evaluators import PublicationEvaluator
from common.evaluators.publication_evaluator import PublicationThresholds


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


def print_results_table(results: list[dict]) -> None:
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
        m = r["evaluation"].metrics
        print(
            f"{r['title'][:34]:<35} "
            f"{m['impressions']:<10,} "
            f"{m['clicks']:<8,} "
            f"{m['saves']:<8,} "
            f"{m['ctr']:<7.2f}% "
            f"{m['save_rate']:<7.2f}% "
            f"{r['evaluation'].action.value:<18} "
            f"{r['evaluation'].reason}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate organic pin performance and recommend actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Evaluate all pins (dry run):
    python publication_manager.py evaluate

  With custom thresholds:
    python publication_manager.py evaluate --min-impressions 1000 --high-ctr 2.0

  Filter to only actionable results:
    python publication_manager.py evaluate --actionable

  Output as JSON:
    python publication_manager.py evaluate --json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate organic pin performance")
    eval_parser.add_argument("--days", type=int, default=7, help="Days of metrics (default: 7)")
    eval_parser.add_argument("--limit", type=int, help="Limit number of pins to evaluate")
    eval_parser.add_argument("--min-impressions", type=int, default=500, help="Min impressions to evaluate (default: 500)")
    eval_parser.add_argument("--high-ctr", type=float, default=1.5, help="High CTR threshold %% (default: 1.5)")
    eval_parser.add_argument("--low-ctr", type=float, default=0.5, help="Low CTR threshold %% (default: 0.5)")
    eval_parser.add_argument("--high-save-rate", type=float, default=2.0, help="High save rate threshold %% (default: 2.0)")
    eval_parser.add_argument("--low-save-rate", type=float, default=0.5, help="Low save rate threshold %% (default: 0.5)")
    eval_parser.add_argument("--actionable", action="store_true", help="Only show pins with recommended actions")
    eval_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.command == "evaluate":
        thresholds = PublicationThresholds(
            min_impressions=args.min_impressions,
            high_ctr=args.high_ctr,
            low_ctr=args.low_ctr,
            high_save_rate=args.high_save_rate,
            low_save_rate=args.low_save_rate,
        )
        evaluator = PublicationEvaluator(thresholds)

        print("Fetching pins...")
        pins = fetch_all_pins(access_token)
        if args.limit:
            pins = pins[: args.limit]
        print(f"Found {len(pins)} pins. Fetching analytics ({args.days} days)...\n")

        results = []
        for i, pin in enumerate(pins):
            pin_id = pin.get("id")
            title = pin.get("title", "Untitled") or "Untitled"
            print(f"  [{i + 1}/{len(pins)}] {pin_id}")

            metrics = fetch_pin_analytics(access_token, pin_id, args.days)
            evaluation = evaluator.evaluate(metrics)

            results.append({
                "pin_id": pin_id,
                "title": title,
                "link": pin.get("link", ""),
                "evaluation": evaluation,
            })

            time.sleep(0.3)

        if args.actionable:
            results = [r for r in results if r["evaluation"].action.value != "none"]

        if args.json:
            json_results = [
                {
                    "pin_id": r["pin_id"],
                    "title": r["title"],
                    "action": r["evaluation"].action.value,
                    "reason": r["evaluation"].reason,
                    "metrics": r["evaluation"].metrics,
                }
                for r in results
            ]
            print(json.dumps(json_results, indent=2))
        else:
            # Summary
            actions = {}
            for r in results:
                action = r["evaluation"].action.value
                actions[action] = actions.get(action, 0) + 1

            print(f"\nEvaluated {len(results)} pins:")
            for action, count in sorted(actions.items()):
                print(f"  {action}: {count}")

            print_results_table(results)


if __name__ == "__main__":
    main()
