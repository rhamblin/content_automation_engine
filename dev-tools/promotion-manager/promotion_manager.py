"""Promotion Manager - evaluate and manage Pinterest ad campaigns."""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "get-pin-ids"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "src"))

from auth import PINTEREST_API_URL, get_access_token
from common.evaluators import PromotionEvaluator
from common.evaluators.promotion_evaluator import PromotionThresholds


class PinterestCampaignClient:
    """Pinterest Ads API client — read/write operations only."""

    def __init__(self, access_token: str):
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_ad_accounts(self) -> list[dict]:
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts", headers=self.headers
        )
        if not response.ok:
            print(f"Failed to fetch ad accounts: {response.status_code} - {response.text}")
            return []
        return response.json().get("items", [])

    def get_campaigns(
        self, ad_account_id: str, status_filter: list[str] | None = None
    ) -> list[dict]:
        params = {}
        if status_filter:
            params["entity_statuses"] = ",".join(status_filter)

        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers=self.headers,
            params=params,
        )
        if not response.ok:
            print(f"Failed to fetch campaigns: {response.status_code} - {response.text}")
            return []
        return response.json().get("items", [])

    def get_campaign_analytics(
        self, ad_account_id: str, campaign_ids: list[str], days: int = 7
    ) -> dict:
        if not campaign_ids:
            return {}

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)

        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns/analytics",
            headers=self.headers,
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "campaign_ids": ",".join(campaign_ids),
                "columns": "CAMPAIGN_NAME,TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
                "granularity": "TOTAL",
            },
        )

        if not response.ok:
            print(f"Failed to fetch analytics: {response.status_code} - {response.text}")
            return {}

        result = {}
        for item in response.json():
            campaign_id = item.get("CAMPAIGN_ID")
            if campaign_id:
                result[campaign_id] = {
                    "impressions": item.get("TOTAL_IMPRESSION", 0) or 0,
                    "clicks": item.get("TOTAL_CLICKTHROUGH", 0) or 0,
                    "spend": item.get("SPEND_IN_DOLLAR", 0) or 0,
                    "ctr": item.get("CTR", 0) or 0,
                    "cpc": item.get("ECPC_IN_DOLLAR", 0) or 0,
                }
        return result

    def update_campaign_status(
        self, ad_account_id: str, campaign_id: str, status: str
    ) -> bool:
        response = requests.patch(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers={**self.headers, "Content-Type": "application/json"},
            json=[{"id": campaign_id, "status": status}],
        )
        if not response.ok:
            print(f"Failed to update campaign: {response.status_code} - {response.text}")
            return False
        print(f"  Campaign {campaign_id} status updated to {status}")
        return True

    def update_campaign_budget(
        self, ad_account_id: str, campaign_id: str, daily_spend_cap: float
    ) -> bool:
        microdollars = int(daily_spend_cap * 1_000_000)
        response = requests.patch(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers={**self.headers, "Content-Type": "application/json"},
            json=[{"id": campaign_id, "daily_spend_cap": microdollars}],
        )
        if not response.ok:
            print(f"Failed to update budget: {response.status_code} - {response.text}")
            return False
        print(f"  Campaign {campaign_id} daily budget updated to ${daily_spend_cap:.2f}")
        return True


class PromotionManager:
    """Orchestrator — fetches data, delegates decisions to evaluator, executes actions."""

    def __init__(
        self,
        client: PinterestCampaignClient,
        evaluator: PromotionEvaluator,
    ):
        self.client = client
        self.evaluator = evaluator

    def list_campaigns(
        self, ad_account_id: str, days: int = 7, status_filter: list[str] | None = None
    ) -> list[dict]:
        campaigns = self.client.get_campaigns(ad_account_id, status_filter)
        if not campaigns:
            return []

        campaign_ids = [c["id"] for c in campaigns]
        analytics = self.client.get_campaign_analytics(ad_account_id, campaign_ids, days)

        result = []
        for c in campaigns:
            cid = c["id"]
            metrics = analytics.get(cid, {})
            result.append({
                "id": cid,
                "name": c.get("name", "Unknown"),
                "status": c.get("status", "UNKNOWN"),
                "daily_spend_cap": c.get("daily_spend_cap", 0) / 1_000_000,
                "lifetime_spend_cap": c.get("lifetime_spend_cap", 0) / 1_000_000,
                "impressions": metrics.get("impressions", 0),
                "clicks": metrics.get("clicks", 0),
                "spend": metrics.get("spend", 0),
                "ctr": metrics.get("ctr", 0),
                "cpc": metrics.get("cpc", 0),
            })

        return result

    def evaluate_campaigns(
        self, ad_account_id: str, days: int = 7
    ) -> list[dict]:
        """Evaluate all active campaigns and return recommended actions."""
        campaigns = self.list_campaigns(ad_account_id, days, status_filter=["ACTIVE"])
        results = []

        for c in campaigns:
            # Estimate days_active from campaign data (simplification)
            metrics = {
                "impressions": c["impressions"],
                "clicks": c["clicks"],
                "spend": c["spend"],
                "ctr": c["ctr"],
                "cpc": c["cpc"],
                "days_active": days,
                "lifetime_budget": c["lifetime_spend_cap"],
            }

            evaluation = self.evaluator.evaluate(metrics)
            results.append({
                "campaign_id": c["id"],
                "campaign_name": c["name"],
                "evaluation": evaluation,
                "current_budget": c["daily_spend_cap"],
            })

        return results

    def execute_actions(
        self, ad_account_id: str, results: list[dict], budget_increase_pct: float = 25
    ) -> None:
        """Execute recommended actions on campaigns."""
        for r in results:
            action = r["evaluation"].action.value
            campaign_id = r["campaign_id"]

            if action == "pause":
                self.client.update_campaign_status(ad_account_id, campaign_id, "PAUSED")

            elif action == "remove":
                self.client.update_campaign_status(ad_account_id, campaign_id, "PAUSED")
                print(f"  Campaign {campaign_id} removed (paused + flagged)")

            elif action == "adjust":
                adjustment = r["evaluation"].payload.get("adjustment", "")
                if adjustment == "increase_budget" and r["current_budget"] > 0:
                    new_budget = r["current_budget"] * (1 + budget_increase_pct / 100)
                    self.client.update_campaign_budget(
                        ad_account_id, campaign_id, new_budget
                    )


def print_campaigns_table(campaigns: list[dict]) -> None:
    if not campaigns:
        print("No campaigns found.")
        return

    print(
        f"\n{'Name':<40} {'Status':<10} {'Budget':<10} {'Impr':<10} "
        f"{'Clicks':<8} {'CTR':<8} {'CPC':<8} {'Spend':<10}"
    )
    print("-" * 114)

    for c in campaigns:
        print(
            f"{c['name'][:39]:<40} "
            f"{c['status'][:8]:<10} "
            f"${c['daily_spend_cap']:<9.2f} "
            f"{c['impressions']:<10,} "
            f"{c['clicks']:<8,} "
            f"{c['ctr']:<7.2f}% "
            f"${c['cpc']:<7.2f} "
            f"${c['spend']:<9.2f}"
        )


def print_evaluation_table(results: list[dict]) -> None:
    if not results:
        print("No actions recommended.")
        return

    print(
        f"\n{'Campaign':<35} {'Action':<12} {'CTR':<8} {'CPC':<8} {'Reason'}"
    )
    print("-" * 120)

    for r in results:
        m = r["evaluation"].metrics
        print(
            f"{r['campaign_name'][:34]:<35} "
            f"{r['evaluation'].action.value:<12} "
            f"{m.get('ctr', 0):<7.2f}% "
            f"${m.get('cpc', 0):<7.2f} "
            f"{r['evaluation'].reason}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Pinterest Promotion Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List campaigns:
    python promotion_manager.py list

  Evaluate campaigns (dry run):
    python promotion_manager.py evaluate

  Evaluate and execute:
    python promotion_manager.py evaluate --execute

  Pause a campaign:
    python promotion_manager.py pause --campaign-id 12345

  Start a campaign:
    python promotion_manager.py start --campaign-id 12345

  Set budget:
    python promotion_manager.py budget --campaign-id 12345 --amount 50.00

  Custom thresholds:
    python promotion_manager.py evaluate --target-cpc 1.50 --high-ctr 3.0
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List campaigns with metrics")
    list_parser.add_argument("--days", type=int, default=7, help="Days of metrics (default: 7)")
    list_parser.add_argument("--status", choices=["all", "active", "paused", "archived"], default="all")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate campaigns and recommend actions")
    eval_parser.add_argument("--days", type=int, default=7, help="Days of metrics (default: 7)")
    eval_parser.add_argument("--execute", action="store_true", help="Execute recommended actions")
    eval_parser.add_argument("--target-cpc", type=float, default=2.0, help="Target CPC (default: $2.00)")
    eval_parser.add_argument("--high-ctr", type=float, default=2.0, help="High CTR threshold %% (default: 2.0)")
    eval_parser.add_argument("--low-ctr", type=float, default=0.5, help="Low CTR threshold %% (default: 0.5)")
    eval_parser.add_argument("--min-impressions", type=int, default=1000, help="Min impressions (default: 1000)")
    eval_parser.add_argument("--budget-increase", type=float, default=25, help="Budget increase %% (default: 25)")
    eval_parser.add_argument("--actionable", action="store_true", help="Only show actionable results")
    eval_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a campaign")
    pause_parser.add_argument("--campaign-id", required=True)

    # Start command
    start_parser = subparsers.add_parser("start", help="Start/resume a campaign")
    start_parser.add_argument("--campaign-id", required=True)

    # Budget command
    budget_parser = subparsers.add_parser("budget", help="Set campaign budget")
    budget_parser.add_argument("--campaign-id", required=True)
    budget_parser.add_argument("--amount", type=float, required=True, help="Daily budget in dollars")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    client = PinterestCampaignClient(access_token)

    # Get ad account
    ad_accounts = client.get_ad_accounts()
    if not ad_accounts:
        print("No ad accounts found")
        sys.exit(1)

    ad_account_id = ad_accounts[0]["id"]
    print(f"Using ad account: {ad_account_id}")

    if args.command == "list":
        status_filter = None if args.status == "all" else [args.status.upper()]
        thresholds = PromotionThresholds()
        evaluator = PromotionEvaluator(thresholds)
        manager = PromotionManager(client, evaluator)
        campaigns = manager.list_campaigns(ad_account_id, args.days, status_filter)

        if args.json:
            print(json.dumps(campaigns, indent=2))
        else:
            print_campaigns_table(campaigns)

    elif args.command == "evaluate":
        thresholds = PromotionThresholds(
            target_cpc=args.target_cpc,
            high_ctr=args.high_ctr,
            low_ctr=args.low_ctr,
            min_impressions=args.min_impressions,
        )
        evaluator = PromotionEvaluator(thresholds)
        manager = PromotionManager(client, evaluator)

        results = manager.evaluate_campaigns(ad_account_id, args.days)

        if args.actionable:
            results = [r for r in results if r["evaluation"].action.value != "none"]

        if args.json:
            json_results = [
                {
                    "campaign_id": r["campaign_id"],
                    "campaign_name": r["campaign_name"],
                    "action": r["evaluation"].action.value,
                    "reason": r["evaluation"].reason,
                    "metrics": r["evaluation"].metrics,
                    "payload": r["evaluation"].payload,
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

            print(f"\nEvaluated {len(results)} active campaigns:")
            for action, count in sorted(actions.items()):
                print(f"  {action}: {count}")

            print_evaluation_table(results)

        if args.execute:
            actionable = [r for r in results if r["evaluation"].action.value != "none"]
            if actionable:
                print(f"\nExecuting {len(actionable)} action(s)...")
                manager.execute_actions(ad_account_id, actionable, args.budget_increase)
            else:
                print("\nNo actions to execute.")
        elif any(r["evaluation"].action.value != "none" for r in results):
            print("\n[DRY RUN] Run with --execute to apply changes.")

    elif args.command == "pause":
        client.update_campaign_status(ad_account_id, args.campaign_id, "PAUSED")

    elif args.command == "start":
        client.update_campaign_status(ad_account_id, args.campaign_id, "ACTIVE")

    elif args.command == "budget":
        client.update_campaign_budget(ad_account_id, args.campaign_id, args.amount)


if __name__ == "__main__":
    main()
