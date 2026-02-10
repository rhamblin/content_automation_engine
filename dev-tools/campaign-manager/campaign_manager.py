"""Pinterest Campaign Manager - start, stop, and adjust campaigns based on metrics."""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "get-pin-ids"))
from auth import PINTEREST_API_URL, get_access_token

# Default thresholds for auto-actions
DEFAULT_THRESHOLDS = {
    "pause_ctr_below": 0.5,  # Pause if CTR < 0.5%
    "extend_ctr_above": 2.0,  # Extend budget if CTR > 2%
    "pause_cpc_above": 2.0,  # Pause if CPC > $2.00
    "min_impressions": 1000,  # Need at least 1000 impressions to evaluate
    "budget_increase_pct": 25,  # Increase budget by 25%
}


class CampaignManager:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    # =========================================================================
    # Read Operations
    # =========================================================================

    def get_ad_accounts(self) -> list[dict]:
        """Fetch all ad accounts."""
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts",
            headers=self.headers,
        )
        if not response.ok:
            print(
                f"Failed to fetch ad accounts: {response.status_code} - {response.text}"
            )
            return []
        return response.json().get("items", [])

    def get_campaigns(self, ad_account_id: str) -> list[dict]:
        """Fetch all campaigns for an ad account."""
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers=self.headers,
        )
        if not response.ok:
            print(
                f"Failed to fetch campaigns: {response.status_code} - {response.text}"
            )
            return []
        return response.json().get("items", [])

    def get_campaign_analytics(
        self, ad_account_id: str, campaign_ids: list[str], days: int = 7
    ) -> dict:
        """Fetch analytics for campaigns."""
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
                "columns": "CAMPAIGN_NAME,IMPRESSION,CLICKTHROUGH,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
                "granularity": "TOTAL",
            },
        )

        if not response.ok:
            print(
                f"Failed to fetch analytics: {response.status_code} - {response.text}"
            )
            return {}

        # Convert to dict keyed by campaign_id
        result = {}
        for item in response.json():
            campaign_id = item.get("CAMPAIGN_ID")
            if campaign_id:
                result[campaign_id] = {
                    "impressions": item.get("IMPRESSION", 0),
                    "clicks": item.get("CLICKTHROUGH", 0),
                    "spend": item.get("SPEND_IN_DOLLAR", 0),
                    "ctr": item.get("CTR", 0),
                    "cpc": item.get("ECPC_IN_DOLLAR", 0),
                }
        return result

    # =========================================================================
    # Write Operations
    # =========================================================================

    def update_campaign_status(
        self, ad_account_id: str, campaign_id: str, status: str
    ) -> bool:
        """Update campaign status (ACTIVE, PAUSED)."""
        response = requests.patch(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers={**self.headers, "Content-Type": "application/json"},
            json=[{"id": campaign_id, "status": status}],
        )

        if not response.ok:
            print(
                f"Failed to update campaign: {response.status_code} - {response.text}"
            )
            return False

        print(f"  Campaign {campaign_id} status updated to {status}")
        return True

    def update_campaign_budget(
        self, ad_account_id: str, campaign_id: str, daily_spend_cap: float
    ) -> bool:
        """Update campaign daily spend cap (in microdollars)."""
        # Pinterest API uses microdollars (1 dollar = 1,000,000 microdollars)
        microdollars = int(daily_spend_cap * 1_000_000)

        response = requests.patch(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers={**self.headers, "Content-Type": "application/json"},
            json=[{"id": campaign_id, "daily_spend_cap": microdollars}],
        )

        if not response.ok:
            print(f"Failed to update budget: {response.status_code} - {response.text}")
            return False

        print(
            f"  Campaign {campaign_id} daily budget updated to ${daily_spend_cap:.2f}"
        )
        return True

    # =========================================================================
    # High-Level Actions
    # =========================================================================

    def list_campaigns(self, ad_account_id: str, days: int = 7) -> list[dict]:
        """List campaigns with their current metrics."""
        campaigns = self.get_campaigns(ad_account_id)
        if not campaigns:
            return []

        campaign_ids = [c["id"] for c in campaigns]
        analytics = self.get_campaign_analytics(ad_account_id, campaign_ids, days)

        result = []
        for c in campaigns:
            cid = c["id"]
            metrics = analytics.get(cid, {})
            result.append(
                {
                    "id": cid,
                    "name": c.get("name", "Unknown"),
                    "status": c.get("status", "UNKNOWN"),
                    "daily_spend_cap": c.get("daily_spend_cap", 0)
                    / 1_000_000,  # Convert from microdollars
                    "lifetime_spend_cap": c.get("lifetime_spend_cap", 0) / 1_000_000,
                    "impressions": metrics.get("impressions", 0),
                    "clicks": metrics.get("clicks", 0),
                    "spend": metrics.get("spend", 0),
                    "ctr": metrics.get("ctr", 0),
                    "cpc": metrics.get("cpc", 0),
                }
            )

        return result

    def pause_campaign(self, ad_account_id: str, campaign_id: str) -> bool:
        """Pause a campaign."""
        return self.update_campaign_status(ad_account_id, campaign_id, "PAUSED")

    def start_campaign(self, ad_account_id: str, campaign_id: str) -> bool:
        """Start/resume a campaign."""
        return self.update_campaign_status(ad_account_id, campaign_id, "ACTIVE")

    def extend_budget(
        self, ad_account_id: str, campaign_id: str, increase_pct: float = 25
    ) -> bool:
        """Increase campaign budget by percentage."""
        campaigns = self.get_campaigns(ad_account_id)
        campaign = next((c for c in campaigns if c["id"] == campaign_id), None)

        if not campaign:
            print(f"Campaign {campaign_id} not found")
            return False

        current_budget = campaign.get("daily_spend_cap", 0) / 1_000_000
        if current_budget == 0:
            print(f"Campaign {campaign_id} has no daily spend cap set")
            return False

        new_budget = current_budget * (1 + increase_pct / 100)
        return self.update_campaign_budget(ad_account_id, campaign_id, new_budget)

    def auto_optimize(
        self, ad_account_id: str, thresholds: dict | None = None, dry_run: bool = True
    ) -> list[dict]:
        """Auto-optimize campaigns based on metrics."""
        thresholds = thresholds or DEFAULT_THRESHOLDS
        campaigns = self.list_campaigns(ad_account_id)
        actions = []

        print(f"\nAnalyzing {len(campaigns)} campaigns...")
        print(
            f"Thresholds: CTR pause < {thresholds['pause_ctr_below']}%, "
            f"extend > {thresholds['extend_ctr_above']}%, "
            f"CPC pause > ${thresholds['pause_cpc_above']}"
        )
        print()

        for c in campaigns:
            action = None
            reason = None

            # Skip if not enough data
            if c["impressions"] < thresholds["min_impressions"]:
                continue

            # Check pause conditions
            if c["status"] == "ACTIVE":
                if c["ctr"] < thresholds["pause_ctr_below"]:
                    action = "PAUSE"
                    reason = f"CTR {c['ctr']:.2f}% < {thresholds['pause_ctr_below']}%"
                elif c["cpc"] > thresholds["pause_cpc_above"]:
                    action = "PAUSE"
                    reason = f"CPC ${c['cpc']:.2f} > ${thresholds['pause_cpc_above']}"
                elif c["ctr"] > thresholds["extend_ctr_above"]:
                    action = "EXTEND_BUDGET"
                    reason = f"CTR {c['ctr']:.2f}% > {thresholds['extend_ctr_above']}%"

            if action:
                actions.append(
                    {
                        "campaign_id": c["id"],
                        "campaign_name": c["name"],
                        "action": action,
                        "reason": reason,
                        "current_status": c["status"],
                        "current_budget": c["daily_spend_cap"],
                        "metrics": {
                            "impressions": c["impressions"],
                            "clicks": c["clicks"],
                            "ctr": c["ctr"],
                            "cpc": c["cpc"],
                            "spend": c["spend"],
                        },
                    }
                )

                print(f"  {c['name'][:40]}")
                print(f"    Action: {action}")
                print(f"    Reason: {reason}")
                print(
                    f"    Metrics: {c['impressions']:,} imp, {c['ctr']:.2f}% CTR, ${c['cpc']:.2f} CPC"
                )
                print()

        if not actions:
            print("No actions recommended based on current thresholds.")
            return actions

        if dry_run:
            print(f"\n[DRY RUN] {len(actions)} action(s) would be taken.")
            print("Run with --execute to apply changes.")
        else:
            print(f"\nExecuting {len(actions)} action(s)...")
            for a in actions:
                if a["action"] == "PAUSE":
                    self.pause_campaign(ad_account_id, a["campaign_id"])
                elif a["action"] == "EXTEND_BUDGET":
                    self.extend_budget(
                        ad_account_id,
                        a["campaign_id"],
                        thresholds["budget_increase_pct"],
                    )

        return actions


def print_campaigns_table(campaigns: list[dict]):
    """Print campaigns in a formatted table."""
    if not campaigns:
        print("No campaigns found.")
        return

    print(
        f"\n{'Name':<40} {'Status':<10} {'Budget':<10} {'Impr':<10} {'Clicks':<8} {'CTR':<8} {'CPC':<8} {'Spend':<10}"
    )
    print("-" * 114)

    for c in campaigns:
        status_display = c["status"][:8]
        print(
            f"{c['name'][:39]:<40} "
            f"{status_display:<10} "
            f"${c['daily_spend_cap']:<9.2f} "
            f"{c['impressions']:<10,} "
            f"{c['clicks']:<8,} "
            f"{c['ctr']:<7.2f}% "
            f"${c['cpc']:<7.2f} "
            f"${c['spend']:<9.2f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Pinterest Campaign Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List campaigns:
    python campaign_manager.py list

  Pause a campaign:
    python campaign_manager.py pause --campaign-id 12345

  Start a campaign:
    python campaign_manager.py start --campaign-id 12345

  Extend budget by 25%:
    python campaign_manager.py extend --campaign-id 12345 --increase 25

  Set specific budget:
    python campaign_manager.py budget --campaign-id 12345 --amount 50.00

  Auto-optimize (dry run):
    python campaign_manager.py auto

  Auto-optimize (execute):
    python campaign_manager.py auto --execute

  Custom thresholds:
    python campaign_manager.py auto --pause-ctr 0.3 --extend-ctr 3.0 --execute
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List all campaigns with metrics")
    list_parser.add_argument(
        "--days", type=int, default=7, help="Days of metrics (default: 7)"
    )
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a campaign")
    pause_parser.add_argument(
        "--campaign-id", required=True, help="Campaign ID to pause"
    )

    # Start command
    start_parser = subparsers.add_parser("start", help="Start/resume a campaign")
    start_parser.add_argument(
        "--campaign-id", required=True, help="Campaign ID to start"
    )

    # Extend command
    extend_parser = subparsers.add_parser("extend", help="Extend campaign budget")
    extend_parser.add_argument("--campaign-id", required=True, help="Campaign ID")
    extend_parser.add_argument(
        "--increase", type=float, default=25, help="Percentage increase (default: 25)"
    )

    # Budget command
    budget_parser = subparsers.add_parser("budget", help="Set campaign budget")
    budget_parser.add_argument("--campaign-id", required=True, help="Campaign ID")
    budget_parser.add_argument(
        "--amount", type=float, required=True, help="Daily budget in dollars"
    )

    # Auto command
    auto_parser = subparsers.add_parser("auto", help="Auto-optimize based on metrics")
    auto_parser.add_argument(
        "--execute", action="store_true", help="Execute actions (default is dry run)"
    )
    auto_parser.add_argument(
        "--pause-ctr", type=float, default=0.5, help="Pause if CTR below (default: 0.5)"
    )
    auto_parser.add_argument(
        "--extend-ctr",
        type=float,
        default=2.0,
        help="Extend if CTR above (default: 2.0)",
    )
    auto_parser.add_argument(
        "--pause-cpc", type=float, default=2.0, help="Pause if CPC above (default: 2.0)"
    )
    auto_parser.add_argument(
        "--min-impressions", type=int, default=1000, help="Min impressions to evaluate"
    )
    auto_parser.add_argument(
        "--budget-increase",
        type=float,
        default=25,
        help="Budget increase % (default: 25)",
    )
    auto_parser.add_argument(
        "--json", action="store_true", help="Output actions as JSON"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    manager = CampaignManager(access_token)

    # Get ad account
    ad_accounts = manager.get_ad_accounts()
    if not ad_accounts:
        print("No ad accounts found")
        sys.exit(1)

    ad_account_id = ad_accounts[0]["id"]
    print(f"Using ad account: {ad_account_id}")

    # Execute command
    if args.command == "list":
        campaigns = manager.list_campaigns(ad_account_id, args.days)
        if args.json:
            print(json.dumps(campaigns, indent=2))
        else:
            print_campaigns_table(campaigns)

    elif args.command == "pause":
        manager.pause_campaign(ad_account_id, args.campaign_id)

    elif args.command == "start":
        manager.start_campaign(ad_account_id, args.campaign_id)

    elif args.command == "extend":
        manager.extend_budget(ad_account_id, args.campaign_id, args.increase)

    elif args.command == "budget":
        manager.update_campaign_budget(ad_account_id, args.campaign_id, args.amount)

    elif args.command == "auto":
        thresholds = {
            "pause_ctr_below": args.pause_ctr,
            "extend_ctr_above": args.extend_ctr,
            "pause_cpc_above": args.pause_cpc,
            "min_impressions": args.min_impressions,
            "budget_increase_pct": args.budget_increase,
        }
        actions = manager.auto_optimize(
            ad_account_id,
            thresholds=thresholds,
            dry_run=not args.execute,
        )
        if args.json:
            print(json.dumps(actions, indent=2))


if __name__ == "__main__":
    main()
